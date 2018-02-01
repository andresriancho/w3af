pipeline {
  agent any

  environment {
    TAG = "REPOSITORY/IMAGE:TAG"
  }

  stages {
    stage("Build") {
      steps {
        sh """
           cp extras/docker/Dockerfile . && \
           cp extras/docker/.dockerignore . && \
           docker build -t ${TAG} .
           """
      }
    }

    stage("Push") {
      steps {
        sh "docker push ${TAG}"
      }
    }

    stage("Cleanup") {
      steps {
        sh """
           rm -rf Dockerfile && \
           rm -rf .dockerignore
           """
      }
    }
  }
}
