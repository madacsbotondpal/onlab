FROM robot_base

EXPOSE 4321/tcp

CMD ["python3", "logic.py"]
