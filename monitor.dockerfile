FROM robot_base

EXPOSE 5432/tcp

CMD ["python2.7", "monitor.py"]
