import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import toml
from pydantic import BaseModel

from utils.pydantic_settings_data_class import Configuration

LOGS_PATH = 'logs'
LOGGER_NAME = 'getting_tabular_data_from_pdf'
logger = logging.getLogger(LOGGER_NAME)


class PathProject(BaseModel):
    fine_reader_path: str = r'C:\Program Files (x86)\ABBYY FineReader 15\FineReader.exe'
    temp_dir: str = r'builds\temp'


class LoggerConfig(BaseModel):
    folder: str = LOGS_PATH
    level: int = logging.INFO
    environment: str = 'DEV'


class Tesseract(BaseModel):
    tesseract_path: str = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class TelebotConfig(BaseModel):
    token: str = ''


class PopplerConfig(BaseModel):
    poppler_path: str = r'utils\poppler-23.01.0\Library\bin'


class ProjectConfig(Configuration):
    path_project: PathProject = PathProject()
    logger: LoggerConfig = LoggerConfig()
    tesseract: Tesseract = Tesseract()
    telebot_config: TelebotConfig = TelebotConfig()
    poppler_config: PopplerConfig = PopplerConfig()

def setup_logger():
    log_folder = Path(config_class.logger.folder)
    formatter = logging.Formatter('%(asctime)-15s\t%(levelname)s\t%(module)s: %(message)s')
    root = logging.getLogger()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.level = config_class.logger.level
    console_handler.setFormatter(formatter)

    rotating_handler = TimedRotatingFileHandler(
        filename=log_folder.joinpath(f'{LOGGER_NAME}.log'),
        encoding='utf-8',
        when='W6',
        interval=1,
        backupCount=30
    )
    rotating_handler.level = config_class.logger.level
    rotating_handler.setFormatter(formatter)

    root.level = config_class.logger.level
    root.addHandler(console_handler)
    root.addHandler(rotating_handler)


config_class = ProjectConfig()
setup_logger()
with open(r'config/configuration.toml', 'w') as file:
    toml.dump(config_class.model_dump(), file)
