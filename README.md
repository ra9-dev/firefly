# Firefly Word Count

This project is an assignment project to calculate maximum occuring words in list of blogs

## Prerequisites
The following softwares should be installed in the machine:
> **Python 3.11**

## Running Locally
1. Install Poetry (package manager for python)
    - *if your* **pip** *is mapped to* `pip`
        ```
        pip install poetry==1.7.1
        ```
    - *if your* **pip** *is mapped to* `pip3`
        ```
        pip3 install poetry==1.7.1
        ```
2. Clone the repository
    - using **HTTP**
        ```
        git clone https://github.com/ra9-dev/firefly.git
        ```
    - **or** using **SSH**
        ```
        git clone git@github.com:ra9-dev/firefly.git
        ```
3. Go to the directory folder
    ```
    cd firefly
    ```
4. Finally execute:

    *This will take care of all package installations through installation manager*
    ```
    ./run.sh
    ```
    *To run multiple instances of this script concurrently, execute the above command in different shell window*

## Points to Note
1. Execution of one instance of the script can take around ~1-2 minutes. So please don't exit.
2. For now, keeping in mind the local development and execution, the batch processing has been set to 15 per batch.
    - *You can keep running the script to fetch more articles.*

### ToDos
1. If lock file is existing from more than ~2 minutes, we can expire the lock.
    
    *This will be useful if someone kills the script in-between processing*
2. Expose `BATCH_SIZE` as an environment variable so it can be customised as per requirements.