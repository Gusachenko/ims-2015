# ism-2015
Курс "Технологии хранения данных"

Тема: Разработка объектного хранилища на основе <b>GLusterFS</b>.

Установка зависимостей

~~~
$ sudo apt-get install mongodb python-pip python-dev

$ wget -qO- https://get.docker.com/ | sh
$ sudo usermod -aG docker %user%

$ pip install -r requirements.txt
$ wget https://dl.bintray.com/mitchellh/vagrant/vagrant_1.6.0_x86_64.deb
$ sudo dpkg -i vagrant_1.6.0_x86_64.deb
~~~

####Конфигурирование

Используйте config.yml

Поместите его в /etc/pgluster

Также туда поместите Vagruntfile

Рекомендуется поместить ключи в /etc/pgluster/key/

Структура config.yml
~~~
glusterfs:
      vol: ims # volume name
      brick: "/gluster_volume" #brick path
      vagrant_file: "/etc/pgluster/Vagrantfile" # path to Vagrantfile
      server:
          name: glusterfs-server #server name 
          image: "farmatholin/glusterfs-server:latest" #server docker image
          key: "/etc/pgluster/key/open_key" #path to key
          
      client:
          name: glusterfs-client # client name
          image: "farmatholin/glusterfs-client:latest" #client docker image
          workers: 5 #workers count
      web:
          name: nginx-glusterfs # proxy name 
          image: "farmatholin/glusterfs-client-nginx:latest" #proxy docker image
          port: "9092" #client port
mongo:
      name: pgluster #db name 
      host: localhost
      port: 27017
      server_collection: "servers" # server collection
~~~

На удалённой машине нужно установить docker и дать права пользователю
[Установить Docker Linux](http://docs.docker.com/linux/step_one/).

Также нужно добавить пользователю ключ
либо свой и в настройках указать путь, либо key/open_key.pub
~~~
wget -qO- https://get.docker.com/ | sh
sudo usermod -aG docker %user%
~~~

####Запуск сервиса
~~~
$ sudo ./pglusterd.py start
~~~

####Запуск клиента
~~~
$ ./pgluster.py
pgluster> help # получение списка команд
~~~

####Проверка
~~~
curl http://localhost:9092/
"Good morning sir"
~~~

## Использование API

#### Создать объект
Отправить файл

~~~
echo "Hello World" > mytestfile
curl -v -X POST -T mytestfile http://localhost:9092/files/mytestfile
~~~

#### Список файлов
получить список файлов
~~~
curl http://localhost:9092/files
~~~

#### Удалить файл
Удалить файл
~~~
curl -v -X REMOVE http://localhost:9092/files/<object_id>
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

