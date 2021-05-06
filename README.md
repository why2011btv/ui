Install required package
```
pip install -r requirements.txt
```

Command:
```
nohup sudo FLASK_APP=index.py /home/ubuntu/miniconda3/bin/python -m flask run -h 0.0.0.0 -p 80 > flask.out 2>&1 &
nohup sudo /home/ubuntu/miniconda3/bin/tensorboard --logdir=runs/testing_tensorboard_pt --host=0.0.0.0 --port=443 > tensorboard.out 2>&1 &
```

Demo:
Please use Firefox and visit
```
http://100.25.177.30
```

Example Query:
"Beethoven"
"I like Beethoven and Bach"

Link to Demo Script: https://docs.google.com/document/d/17h5m0IVvukZbdxVLIpBhxQ9_WHY1lhoYyxuwyUGxqUo/edit?usp=sharing