from pywinauto.application import Application

from sources.settings import config_class


def recognition_using_fine_reader(path_to_the_recognition_file: str, path_to_save: str):
    """
    Функция запуска UI работы с ABBYY FineReader
    Открывает десктопное приложение, по пути указанной в файле конфигурации проекта.
    Выбирает конвертацию в excel формат и сохраняет файл по указанному пути.

    :param path_to_the_recognition_file: Путь до PDF-файла, который необходимо ковертировать
    :param path_to_save: Путь, конечного файла в формате xlsx
    :return: None
    """
    app = Application().start(config_class.path_project.fine_reader_path)
    # Инициализируем главное окно программы FineReader
    fr_app = app.window(title_re='ABBYY FineReader PDF 15')
    fr_app.wait("ready")
    # fr_app.dump_tree('FRControls_3.txt')

    fr_app.child_window(title="Конвертировать в Microsoft Excel", class_name="Button").click()

    # Инициализируем окно выбора PDF файла для конвертации
    file_window = app.window(title_re="Выберите файлы для конвертации в Microsoft Excel")
    file_window.wait("ready")

    # Вводим путь pdf-файла и нажимаем "Открыть"
    file_window['&Имя файла:Edit'].set_text(path_to_the_recognition_file)
    file_window.wait("ready")
    file_window.child_window(title="&Открыть", class_name="Button").close_click()

    # Нажимаем кнопку Конвертировать в Excel
    fr_app.child_window(title="Конвертировать в Excel", class_name="Button").click()

    # Инициализируем окно сохранения файла в excel
    save_window = app.window(title_re="Сохранить документ как")
    save_window.wait("ready")
    # Вводим путь конечного файла
    save_window['Edit'].set_text(path_to_save)
    # Если стоял checkbox на открытие файла после конвертации - снимаем его
    if save_window['&Открыть документCheckBox'].get_check_state():
        save_window['&Открыть документCheckBox'].click_input()
    # Нажимаем кнопку Сохранить
    save_window.child_window(title="Со&хранить", class_name="Button").close_click()

    # Инициализируем окно процесса конвертации и ожидаем когда оно исчезнет
    convert_window = app.window(title_re="Конвертирование")
    convert_window.wait_not('visible', timeout=60)

    # Закрываем FineReader
    app.kill()
