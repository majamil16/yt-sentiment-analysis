# Youtube Video Sentiment Analysis / NLP

[Project setup](https://dzone.com/articles/data-science-project-folder-structure)

* src: The folder that consists of the source code related to data gathering, data preparation, feature * extraction, etc.
* tests: The folder that consists of the code representing unit tests for code maintained with the src folder.
* models: The folder that consists of files representing trained/retrained models as part of build jobs, etc. The model names can be appropriately set as projectname_date_time or project_build_id (in case the model is created as part of build jobs). Another approach is to store the model files in a separate storage such as AWS S3, Google Cloud Storage, or any other form of storage.
* data: The folder consists of data used for model training/retraining. The data could also be stored in a * separate storage system.
* pipeline: The folder consists of code that's used for retraining and testing the model in an automated manner. These could be docker containers related code, scripts, workflow related code, etc.
* docs: The folder that consists of code related to the product requirement specifications (PRS), technical * design specifications (TDS), etc.

## Overview

Project aim:

* classify text into categories based on transcript / predict video category

* ...

## Testing

    python -m unittest <module_name>

Fill in more details later.
