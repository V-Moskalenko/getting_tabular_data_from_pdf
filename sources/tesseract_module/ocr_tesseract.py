import logging
import os
from datetime import datetime

import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
from PIL import Image

from sources.settings import config_class

pytesseract.pytesseract.tesseract_cmd = config_class.tesseract.tesseract_path


logger = logging.getLogger(__name__)


class RecognitionModule:
    """
    Класс распознавания табличных данных в PDF, с помощью Tesseract-OCR
    """
    __slots__ = ('path_to_pdf', 'degree_of_rotation', 'data_from_pdf')

    def __init__(self, path_to_pdf: str, degree_of_rotation: int):
        """
        Конструктор класса

        :param path_to_pdf: Путь до PDF-файла
        :param degree_of_rotation: Наклон изображения
                                   "Повернуто на 90 градусов влево": 270,
                                   "Перевёрнуто": 180,
                                   "Повернуто на 90 градусов вправо": 90,
                                   "Изображение не наклонено": 0
        """
        self.path_to_pdf = path_to_pdf
        self.degree_of_rotation = degree_of_rotation
        self.data_from_pdf = self.get_data_from_pdf()

    def get_data_from_pdf(self) -> list:
        """
        Функция проходит по каждому листу PDF и поворачивает её на переданный наклон изображения

        :return: На выходе получаем распознанную таблицу с данными
        """
        image_list = self.pdf_to_image()
        image_list = [self.rotate_image(path) for path in image_list]
        all_data = []
        for image in image_list:
            all_data += self.get_table(image)
            os.remove(image)
        return all_data

    def pdf_to_image(self) -> list:
        """
        Конвектируем PDF в PNG рисунок и сохранем его в папку temp.

        :return: Список путей до полученных рисунков
        """
        poppler_path = config_class.poppler_config.poppler_path
        temp_dir = config_class.path_project.temp_dir
        try:
            pages = convert_from_path(self.path_to_pdf, 600, poppler_path=poppler_path)
            pdf_name = os.path.basename(self.path_to_pdf).split('.')[0]
            pdf_name = self.rename_pdf_file(pdf_name)
            save_image = lambda page, count: (path := fr'{temp_dir}\{pdf_name}_page_{count}.png', page.save(path, 'PNG'))
            image_list = [save_image(page, count)[0] for page, count in zip(pages, range(1, len(pages) + 1))]
            return image_list
        except Exception as e:
            logger.error(f'Ошибка при конвертировании pdf файла. Файл - {self.path_to_pdf}. \n Ошибка - {e}.')
            raise e

    def rotate_image(self, image_path: str) -> str:
        """
        Функция поворота изображения

        :param image_path: путь до изображения
        :return: путь до изображения
        """
        try:
            image = Image.open(image_path)
            image_rotate = image.rotate(self.degree_of_rotation, expand=True)
            image_rotate.save(image_path, quality=100)
            image.close()
            return image_path
        except Exception as e:
            logger.error(f'Ошибка при повороте изображения. Изображение - {image_path}. \n Ошибка - {e}.')
            raise e

    def get_table(self, image: str) -> list:
        """
        Получение табличных данных

        :param image: путь до изображения
        :return: таблица с распознынными данными
        """
        try:
            # Подготавливаем изборажение, переводим в ч/б тона
            image = cv2.imread(image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ret, thresh_value = cv2.threshold(image, 180, 255, cv2.THRESH_BINARY_INV)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

            # Находим вертикальные линии
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, np.array(image).shape[1] // 150))
            eroded_image = cv2.erode(thresh_value, vertical_kernel, iterations=3)

            vertical_lines = cv2.dilate(eroded_image, vertical_kernel, iterations=3)

            # Находим горизотальные линии
            hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (np.array(image).shape[1] // 150, 1))
            horizontal_lines = cv2.erode(thresh_value, hor_kernel, iterations=3)
            horizontal_lines = cv2.dilate(horizontal_lines, hor_kernel, iterations=3)

            # Проводим соединение
            vertical_horizontal_lines = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
            vertical_horizontal_lines = cv2.erode(~vertical_horizontal_lines, kernel, iterations=3)

            thresh, vertical_horizontal_lines = cv2.threshold(vertical_horizontal_lines, 128, 255,
                                                              cv2.THRESH_BINARY | cv2.THRESH_OTSU)

            # Получаем кординаты ячеек таблицы
            bitxor = cv2.bitwise_xor(image, vertical_horizontal_lines)
            bitnot = cv2.bitwise_not(bitxor)
            contours, hierarchy = cv2.findContours(vertical_horizontal_lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            coordinates = [(cv2.boundingRect(contour)) for contour in contours]
            coordinates.sort()  # sort by x
            coordinates.sort(key=lambda j: j[1])  # sort by y
            recognized_table = self.get_text_from_image(coordinates, image)
            prepared_table = self.line_preparation(recognized_table)
            return prepared_table
        except Exception as e:
            logger.error(f'Ошибка в основной функции получения данных. \n Ошибка - {e}.')
            raise e

    @staticmethod
    def get_text_from_image(coordinates: list, image) -> list:
        """
        Функция проходит по переданному списку координат, обрезает по ним изображение и проводит её распознавание.
        Распознанные части собираются построчно, взависимости от координыты Y, в итоговый список

        :param coordinates: список координат
        :param image: подготовленный объект ихображения
        :return: список данных, распознанной таблицы
        """
        try:
            recognized_table = []
            prev_y = 0
            row_temp = []
            for coord in coordinates:
                x, y, w, h = coord
                crop_img = image[y:y + h, x:x + w]
                recognized_string = pytesseract.image_to_string(crop_img, lang="rus")
                if prev_y - 10 <= y <= prev_y + 10:  # определение новой строки по координате Y
                    row_temp.append(recognized_string.replace("\n", " "))
                else:
                    recognized_table.append(row_temp)
                    row_temp = []
                    row_temp.append(recognized_string.replace("\n", " "))
                prev_y = y
            return recognized_table
        except Exception as e:
            logger.error(f'Ошибка при получения теста. \n Ошибка - {e}.')
            raise e

    @staticmethod
    def line_preparation(recognized_table: list) -> list:
        """
        Очистка, фильтрация и формирование итоговой строки

        :param recognized_table: очищенный список данных, распознанной таблицы
        :return:
        """
        try:
            prepared_table = []
            table = str.maketrans("", "", "!@#$%^&*_+|+\/:;[]{}<>—-_(),`='")
            for row in recognized_table:
                if len(row) >= 4:
                    row = [i.translate(table).strip() for i in row if 100 > len(i) > 5]
                    prepared_table.append(row)
            return prepared_table
        except Exception as e:
            logger.error(f'Ошибка при очистке и формировании итоговых строк. \n Ошибка - {e}.')
            raise e

    @staticmethod
    def rename_pdf_file(pdf_name: str) -> str:
        """
        Переименование PDF-файла из кириллицы

        :param pdf_name: путь до PDF-файла
        :return: путь до переименованного файла
        """
        if any([ord(i) in range(ord('А'), ord('я')) for i in pdf_name]):
            pdf_name = f'scan_{datetime.now().strftime("%d.%m.%Y_%H.%M")}'
        return pdf_name
