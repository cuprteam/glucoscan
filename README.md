### Glucoscan Overview

### How to run GlucoScan in Docker

 - __Prerequisity__: A linux computer with docker installed
 - Clone the recognizer: `git clone https://github.com/cuprteam/glucoscan`
 - This should result in the following directory structure (printing only the first 2 levels):
```
 $ tree -L 2 --dirsfirst glucoscan/
glucoscan/
├── lcd_digit_recognizer
│   ├── experiments
│   ├── __pycache__
│   ├── recognition
│   ├── visualization
│   ├── web
│   └── __init__.py
├── recognize_seven_segment
│   ├── detectors
│   ├── experiments
│   ├── hackathon_api
│   ├── __pycache__
│   ├── resources
│   ├── utils
│   └── __init__.py
├── build_and_run.sh
├── build.sh
├── Dockerfile
├── glucoscan_entrypoint.sh
├── README.md
├── requirements.txt
└── run.sh

13 directories, 9 files
```
 - Run `build_and_run.sh` - script that builds docker image with glucoscan (by calling `build.sh`) and runs the docker container (by calling `run.sh`)

