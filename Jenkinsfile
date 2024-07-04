pipeline {
    agent any

    environment {
        DOCKERHUB_REPO = 'tiagoluz92/solana-spl-momentum-scanner'
        TAG = "${env.BUILD_NUMBER}"
        APP_NAME = 'solana-spl-momentum-scanner'
        GIT_CREDENTIALS = 'git_hub'
    }

    stages {
        stage('Cleanup Workspace') {
            steps {
                cleanWs()
            }
        }
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM', 
                    branches: [[name: '*/master']],
                    doGenerateSubmoduleConfigurations: false, 
                    extensions: [], 
                    userRemoteConfigs: [[
                        url: 'https://github.com/TiagoLuz9292/solana-spl-momentum-scanner.git', 
                        credentialsId: "${GIT_CREDENTIALS}"
                    ]]
                ])
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
        stage('Cleanup Docker Images') {
            steps {
                script {
                    sh "docker rmi ${env.DOCKERHUB_REPO}-frontend:${env.TAG}"
                    sh "docker rmi ${env.DOCKERHUB_REPO}-backend:${env.TAG}"
                }
            }
        }
    }
}