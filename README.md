# RAG-based Stainless Steel Knowledge Assistant

## Environment Setup

```bash
pip install pipenv
pipenv shell
(stainless-rag-xxxx) pipenv install

# backend
(stainless-rag-xxxx) tmux new -s backend
(stainless-rag-xxxx) python app.py

# frontend
(stainless-rag-xxxx) tmux new -s frontend
(stainless-rag-xxxx) streamlit run frontend.py
```

## AWS EC2 Instance Setup

1. Launch an EC2 instance with the following configuration:
   - AMI: Amazon Linux 2023
   - Security Group: Allow inbound traffic on ports 22 (SSH), 8501 (Streamlit)

2. Connect to the instance via console

3. Install necessary packages:

    ```bash
    # install packages
    sudo dnf update -y
    sudo dnf install -y python3.9 tmux pip

    # aws configure
    aws configure
    > <your_access_key>
    > <your_secret_key>
    > <your_region>
    > json

    # git setting
    ssh-keygen -t ed25519 -C "ec2-aws"
    cat ~/.ssh/id_ed25519.pub
    # paste the public key to GitHub SSH key settings
    git clone git@github.com:AlphaGirls2025/stainless-rag.git

    # project setup
    cd stainless-rag
    pip install pipenv
    pipenv shell
    (stainless-rag-xxxx) pipenv install
    (stainless-rag-xxxx) tmux new -s backend
    (stainless-rag-xxxx) python app.py
    (stainless-rag-xxxx) tmux new -s frontend
    (stainless-rag-xxxx) streamlit run frontend.py
    ```

4. Access the Streamlit app via the public IP of your EC2 instance on port 8501.