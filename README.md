# ism-2015
Курс "Основы технологий хранения данных"

Тема: разработка распределённой, параллельной, линейно масштабируемой файловой системы <b>GLusterFS</b>.

Установка зависимостей

~~~
$ pip install -r requirements.txt
~~~
Запуск 
~~~
$ ./pgluster.py

#check
curl http://localhost:9092/
"Good morning sir"
~~~

## Использование API

#### Создать объект
Отправить файл

~~~
echo "Hello World" > mytestfile
curl -v -X PUT -T mytestfile -H  http://localhost:9093/files
~~~


#### Получение объекта
Можно получить файл выполнив комманду:

~~~
curl -v -X GET -o newfile http://localhost:9093/files/<object_id>
cat newfile
~~~
Участники:

-Марин Владислав 0303

-Гусаченко Глеб 0303

