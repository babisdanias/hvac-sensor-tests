// Same pipeline as the GitHub Actions workflow, for Jenkins.
// Needs the Docker Pipeline plugin (to run inside a python image)
// A venv is used because the container runs as a non-root user, so pip cannot
// write to the system site-packages and ~/.local/bin is not on PATH.
// and the Robot Framework plugin (to show results in Jenkins).

pipeline {
    agent {
        docker { image 'python:3.12-slim' }
    }

    stages {
        stage('Install') {
            steps {
                sh 'python -m venv .venv && .venv/bin/pip install -r requirements.txt'
            }
        }
        stage('Smoke tests') {
            steps {
                sh '.venv/bin/robot --include smoke --outputdir results/smoke tests'
            }
        }
        stage('Full regression') {
            steps {
                sh '.venv/bin/robot --outputdir results/full tests'
            }
        }
    }

    post {
        always {
            robot outputPath: 'results/full', passThreshold: 100.0, unstableThreshold: 90.0
            archiveArtifacts artifacts: 'results/**', allowEmptyArchive: true
        }
    }
}
