import logging
import logging.handlers

def setup_logging(log_level=logging.DEBUG):
    # Create a custom logger
    logger = logging.getLogger('LoudVA')
    if not logger.handlers:
        logger.setLevel(log_level)

        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = logging.handlers.RotatingFileHandler('LoudVA.log', maxBytes=5*1024*1024, backupCount=2)

        # Set levels for handlers
        c_handler.setLevel(log_level)
        f_handler.setLevel(log_level)

        # Create formatters and add them to handlers
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s] - %(message)s')
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s] - %(message)s')
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        logger.propagate = False

    return logger
