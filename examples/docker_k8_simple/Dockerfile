FROM prefecthq/prefect:2-python3.11

COPY giza-0.1.0-py3-none-any.whl ./giza-0.1.0-py3-none-any.whl
RUN pip install giza-0.1.0-py3-none-any.whl --trusted-host pypi.python.org --no-cache-dir

# Add our flow code to the image
COPY action.py /opt/prefect/flows/action.py

# Run our flow script when the container starts
CMD ["python", "flows/action.py"]