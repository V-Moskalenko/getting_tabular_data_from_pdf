import logging
import os

import pandas
from openpyxl.reader.excel import load_workbook
from openpyxl.utils import get_column_letter

from fine_reader_module.pywinauto_fr import recognition_using_fine_reader
from tesseract_module.ocr_tesseract import RecognitionModule

logger = logging.getLogger(__name__)


def recognition_main(pdf_file_path: str, degree_of_rotation: int) -> str:
    # Шаг №1 - произведем распознавание с помощью Тессеракта
    ocr_obj = RecognitionModule(pdf_file_path, degree_of_rotation)
    data_matrix = ocr_obj.data_from_pdf

    # Шаг №2 - сохраним полученные данные в excel
    path_to_save = pdf_file_path.split('.')[0] + '.xlsx'
    convert_data_list_in_excel(data_matrix, path_to_save)

    # Шаг №3 - произведем распознавание с помощью FineReader
    path_to_save_fr = os.path.abspath(pdf_file_path.split('.')[0] + '_fr.xlsx')
    logger.info(f'Абсолютный путь: {path_to_save_fr}')
    recognition_using_fine_reader(os.path.abspath(pdf_file_path), path_to_save_fr)

    # Шаг №4 - сохраним данные в общий excel
    write_finereader_data_to_excel(path_to_save, path_to_save_fr)

    # Шаг №5 - удалим файл excel файл FineReader
    os.remove(path_to_save_fr)
    return path_to_save


def convert_data_list_in_excel(data_matrix: list | pandas.DataFrame, path_to_save: str) -> str:
    sheet_name = 'Данные Tesseract'

    try:
        # Преобразуем матрицу в DataFrame и запишем её на лист
        data_dict = dict(zip(range(1, len(data_matrix) + 1), data_matrix))
        df = pandas.DataFrame.from_dict(data_dict, orient='index')
        df.insert(1, "№", df.index + 1)
        logger.info('Сформировал DF из распознанных данных')
        with pandas.ExcelWriter(path_to_save) as writer:
            df.to_excel(writer, sheet_name=sheet_name, header=False, index=False, engine='openpyxl')
        width_list_data = get_width_column(df)
        if width_list_data:
            resize_column(path_to_save, width_list_data, sheet_name)
        return path_to_save
    except Exception as e:
        logger.error(f'Ошибка в функции convert_data_list_in_excel - {e}')
        raise e


def write_finereader_data_to_excel(path_to_save: str, path_to_save_fr: str) -> str:
    sheet_name = 'Данные FineReader'
    try:
        df_fr = pandas.read_excel(path_to_save_fr)
        with pandas.ExcelWriter(path_to_save, mode="a", if_sheet_exists="replace") as writer:
            df_fr.to_excel(writer, sheet_name=sheet_name, header=False, index=False, engine='openpyxl')
        width_list_data = get_width_column(df_fr)
        if width_list_data:
            resize_column(path_to_save_fr, width_list_data, sheet_name)
        return path_to_save
    except Exception as e:
        logger.error(f'Ошибка в функции write_finereader_data_to_excel - {e}')
        raise e


def resize_column(path: str, width_list: list, sheetname: str):
    try:
        wb = load_workbook(path)
        ws = wb[sheetname]
        ws.column_dimensions['A'].width = 5
        for i, j in zip(range(1, ws.max_column + 1), width_list):
            letter = get_column_letter(i)
            ws.column_dimensions[letter].width = j + 2
        wb.save(path)
    except Exception as e:
        logger.error(f'Ошибка при изменении ширины столбцов в excel - {e}')


def get_width_column(df: pandas.DataFrame):
    try:
        df = df.astype(str)
        width_list = [max([len(i) if i is not None else 0 for i in tuple(df[column])]) for column in
                      tuple(df.columns)]
        return width_list
    except Exception as e:
        logger.error(f'Ошибка при получении ширины столбцов - {e}')


def delete_temp_files(pdf_file: str, excel_file: str):
    try:
        for file in (pdf_file, excel_file):
            os.remove(file)
        logger.info(f'Удалил временные файлы: {pdf_file, excel_file}')
    except Exception as e:
        logger.error(f'Ошибка при удалении временных файлов: {pdf_file, excel_file} ')
