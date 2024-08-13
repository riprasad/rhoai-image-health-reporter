import logger

LOGGER = logger.getLogger(__name__)

def main():

    # Use the LOGGERGER to print messages
    LOGGER.debug("This is a debug message")
    LOGGER.info("This is an info message")
    LOGGER.warning("This is a warning message")
    LOGGER.error("This is an error message")
    LOGGER.critical("This is a critical message")
    
    
    
if __name__ == '__main__':
    main()