# SageMath-MAESC
A repo for building a SageMath microservice Docker image

## Build

Build the image with `build.sh`. Pass in your hostname as an argument (i.e. HOSTNAME/sagemath)

## Running

You can run the image with the following command (replace HOST_PORT,HOST_DIR,HOST_NAME):

`docker run -itd -p HOST_PORT:9602 HOST_NAME/sagemath`

## Usage

/service - this will run your SageMath code and respond with your requested variables.

```
{
  "code": string, the code to run
  "vars": array, should contain the variable names from your code that you want returned
}

* if your variable points to a resource (i.e. image,audio,etc.), it should start with an underscore "_". When /service returns that variable, it will point to the URL where that resource can be retrieved.
