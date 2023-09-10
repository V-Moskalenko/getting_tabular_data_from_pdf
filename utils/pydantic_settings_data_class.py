import toml
import logging
from pathlib import Path
from typing import Any, Type, Dict

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

logger = logging.getLogger(__name__)


class Configuration(BaseSettings):
    """
    Базовый класс конфигурации проекта.
    В файле настроект проекта определяем сабклассы настроек и основной, который будет наследоваться от этого класа.
    При инициализации класса, произойдет чтение файла конфигурации и настройки из переменной среды добавятся в сабклассы,
    по приоритету, от дефолтных значений.
    Если необходимо, чтобы настройка не имела дефолтных значений и без её наличия появлялась ошибка - в сабклассе не
    устанавливаем значение по умолчанию, а в основном классе настроек не вызываем сабкласс.

    Пример использования:
        LOGS_PATH = Path('logs')

        # Определяем сабклассы настроек проекта
        class MongoDB(BaseModel):
            host: str = ''
            port: int = 0
            db: str = ''
            my_collection: str = 'test'
            mechanism: str = ''

        class LoggerConfig(BaseModel):
            folder: Path = LOGS_PATH
            level: int = logging.INFO
            environment: str = 'DEV'

        class Authorization(BaseModel):
            login: str
            password: str

        # Определяем основной класс настроек
        class ProjectConfig(Configuration):
            # Если необходимо заменить директорию или наименования файла конфигурации
            class TomlConfig(Configuration.TomlConfig):
                config_dir_name: str = 'config'
                config_filename: str = 'configuration.toml'

            mongo: MongoDB = MongoDB()
            logger: LogerConfig = LogerConfig()
            auth: Authorization    # Если данных настроек не будет в файле, будет вызвана ошибка

        configuration = ProjectConfig()
        >> configuration.mongo.my_collection -> 'test'

    """
    class TomlConfig:
        """
        Класс чтения файла конфигурации, добавления значений в переменную среду и сбор этих настроект в класс конфигурации
        """
        config_dir_name: str = 'config'
        config_filename: str = 'configuration.toml'

        @staticmethod
        def locate_configuration_directory(config_dir_name: str = 'config') -> Path | None:
            """
            Поиск каталога конфигурации от текущего расположения модуля - вверх.

            :param config_dir_name: Название директории, содержащей файл конфигурации, по умолчанию: "config"
            :return: Путь до директории или None, если католог не обнаружен
            """
            abspath = Path(__file__).absolute()
            for parent in abspath.parents:
                target_path = parent.joinpath(config_dir_name)
                if target_path.exists() and target_path.is_dir():
                    return target_path
            return None

        @staticmethod
        def read_configuration_file(path_configuration_dir: Path, config_filename: str) -> dict[str, Any]:
            """
            Чтение файла конфигурации

            :param path_configuration_dir: Путь до директории содержащей файлы конфигурации, "config"
            :param config_filename: Наименование файла конфигурации, "configuration.toml"
            :return: Словарь настроеку проекта
            """
            with open(path_configuration_dir.joinpath(config_filename), 'r') as file:
                return toml.load(file)

        def __call__(self) -> Dict[str, Any]:
            """
            Чтение файла конфигурации, по указанным атрибутам класса и возврат настроек проекта

            :return: Словарь с настройками проекта
            """
            path_config_dir = self.locate_configuration_directory(self.config_dir_name)
            if path_config_dir:
                try:
                    return self.read_configuration_file(path_config_dir, self.config_filename)
                except FileNotFoundError:
                    logger.debug(
                        fr"Файл конфигурации не найден по следующему пути: {path_config_dir}\{self.config_filename}")
            return {}

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ):
        return (
            init_settings,
            cls.TomlConfig(),
            env_settings,
            file_secret_settings,
        )

