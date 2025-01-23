import logging
import logging.handlers
import Settings as settings

if settings.debug:
    default_level = logging.DEBUG
else:
    default_level = logging.INFO

def setup_logging(log_level=default_level):
    # Create a custom logger
    logger = logging.getLogger('LoudVA')
    if not logger.handlers:
        logger.setLevel(log_level)

        # Stream handler
        c_handler = logging.StreamHandler()
        c_handler.setLevel(log_level)
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s] - %(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)


        # File handler
        # f_handler = logging.handlers.RotatingFileHandler('LoudVA.log', maxBytes=5*1024*1024, backupCount=2)
        # f_handler.setLevel(log_level)
        # f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s] - %(message)s')
        # f_handler.setFormatter(f_format)
        # logger.addHandler(f_handler)

        logger.propagate = False

    return logger
