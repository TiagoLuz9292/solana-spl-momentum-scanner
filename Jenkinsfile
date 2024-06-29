pipeline {
    agent any

    environment {
        DOCKERHUB_REPO = 'tiagoluz92/solana-spl-momentum-scanner'
        TAG = "${env.BUILD_NUMBER}"
        APP_NAME = 'solana-spl-momentum-scanner'
        CONFIG_FILE = '/path/to/config.json'
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/TiagoLuz9292/cicd-project.git'
            }
        }
        stage('Build Frontend') {
            steps {
                script {
                    docker.build("${env.DOCKERHUB_REPO}-frontend:${env.TAG}", "./frontend")
                }
            }
        }
        stage('Build Backend') {
            steps {
                script {
                    docker.build("${env.DOCKERHUB_REPO}-backend:${env.TAG}", "./backend")
                }
            }
        }
        stage('Push Frontend') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'docker_hub') {
                        docker.image("${env.DOCKERHUB_REPO}-frontend:${env.TAG}").push()
                    }
                }
            }
        }
        stage('Push Backend') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'docker_hub') {
                        docker.image("${env.DOCKERHUB_REPO}-backend:${env.TAG}").push()
                    }
                }
            }
        }
    }
}