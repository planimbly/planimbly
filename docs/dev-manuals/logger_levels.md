# Logger levels

|   Name   | Severity | Method                         |
|:--------:|:--------:|--------------------------------|
|  TRACE   |    5     | `logger.trace(message)`        |
|  DEBUG   |    10    | `logger.debug(message)`        |
|   INFO   |    20    | `logger.info(message)`         |
|  ADDED   |    23    | `logger.log("ADDED", message)` |
|  MODEL   |    24    | `logger.log("MODEL", message)` |
| SUCCESS  |    25    | `logger.success(message)`      |
| WARNING  |    30    | `logger.warning(message)`      |
|  ERROR   |    40    | `logger.error(message)`        |
| CRITICAL |    50    | `logger.critical(message)`     |