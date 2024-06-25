pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDENTIALS = credentials('docker_hub')
    }

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', url: 'https://gitlab.com/tiagoluz92/solana-spl-momentum-scanner.git'
            }
        }

        stage('Build Backend Docker Image') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'DOCKER_HUB_CREDENTIALS') {
                        def backendImage = docker.build("tiagoluz92/solana-spl-momentum-scanner:backend", "./backend")
                        backendImage.push()
                    }
                }
            }
        }

        stage('Build Frontend Docker Image') {
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'DOCKER_HUB_CREDENTIALS') {
                        def frontendImage = docker.build("tiagoluz92/solana-spl-momentum-scanner:frontend", "./frontend")
                        frontendImage.push()
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'The build was successful!'
        }
        failure {
            echo 'The build failed.'
        }
    }
}