from loguru import logger

from tucows.log import setup_loguru_logging_intercept
from tucows.models import Base, local_postgres_engine


@logger.catch
def schema_recreation_main():
    engine = local_postgres_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    setup_loguru_logging_intercept()
    schema_recreation_main()
