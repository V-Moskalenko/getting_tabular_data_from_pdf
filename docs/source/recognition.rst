***********************
Модуль основной логике распознования данных
***********************

Расположение
############
sources -> recognition_module -> pandas_work_with_file.py

Описание
########
Модуль запускает распознавание PDF двумя способами: Tesseract-OCR и FineReader.
Далее конвектирует полученные данные в pandas.DataFrame и объединяет их в одном excel-файле на разных листах.
Полученные таблицы форматирует по ширине содержимого столбцов.

Принцип работы модуля
#####################
   1. Производим распознавание с помощью Tesseract
   2. Сохраняем полученные данные в excel
   3. Производим распознование с помощью FineReader
   4. Сохраняем полученные данные с FineReader в excel от Tesseract на отдельном листе
   5. Удаляем файл FineReader

Конфигурация
############
Для работы модуля, необходимы следующие модули:
   1. fine_reader_module -> pywinauto_fr
   2. tesseract_module > ocr_tesseract

Зависимости
###########
pandas 2.1.0, документация: https://pandas.pydata.org/docs/index.html
openpyxl 3.1.2 документация: https://openpyxl.readthedocs.io

Функции модуля
##############

.. automodule:: sources.recognition_module.pandas_work_with_file
      :members: