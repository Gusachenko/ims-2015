# ism-2015
Курс "Основы технологий хранения данных"

Тема: разработка распределённой, параллельной, линейно масштабируемой файловой системы <b>GLusterFS</b>.

Установка зависимостей

~~~
$ pip install -r requirements.txt
~~~

Конфигурирование
Используйте containers.yml

На удалённой машине нужно установить docker и дать права пользователю
[Установить Docker Linux](http://docs.docker.com/linux/step_one/).

Контейнеров должно быть кратно 2

~~~
server:
          name: glusterfs-server # имя контейнера
          image: "farmatholin/glusterfs-server:latest" # докер образ
          credentials:
            - user: user # имя пользователя
              key: "key/open_key" # путь к ключу 
              ip: "192.168.94.134" # ip машины
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
curl -v -X POST -T mytestfile http://localhost:9092/files
~~~


#### Получение объекта
Можно получить файл выполнив комманду:

~~~
curl -v -X GET -o newfile http://localhost:9092/files/<object_id>
cat newfile
~~~
Участники:

-Марин Владислав 0303

-Гусаченко Глеб 0303

