######### Litestar App Dockerfile ############

###############################
######### STAGE BUILD #########
###############################
## Set the base image using Python 3.12 and Debian Bookworm
FROM python:3.11-slim as builder

## Set /tmp as the current working directory
WORKDIR /tmp

## Install poetry via pip
RUN pip install --no-cache-dir --force-reinstall poetry==1.8.2

## Copy pyproject.toml and poetry.lock files (* is included to prevent a crash if poetry.lock is missing)
COPY ./pyproject.toml ./poetry.lock* /tmp/

## Generate a requirements.txt file 
RUN poetry export -f requirements.txt --output requirements.txt

#############################
######### STAGE RUN #########
#############################
## Set the base image using Python 3.12 and Debian Bookworm
FROM python:3.11-slim as runtime

## Copy the requirements.txt file from the previous stage to the current stage
COPY --from=builder /tmp/requirements.txt ./requirements.txt

## Install the backend dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir --upgrade -r ./requirements.txt

## Set the working directory to /src
WORKDIR /src

## Copy only the necessary files to the working directory
COPY ./src /src

## Expose the port the app runs on
EXPOSE 8000

## Run the app with the Litestar CLI
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]