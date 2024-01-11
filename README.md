Projenin çalışabilmesi için geliştirme ortamınızda docker kurulu olması gerekmektedir.

---
Projeyi çalıştırmak için aşağıdaki komutlardan birini kullanabilirsiniz.

```
./run.sh
```

permission denied hatası almanız halinde <mark>chmod +x run.sh</mark> komutunu çalıştırınız.

veya

```
docker compose -f docker-compose.exp.final.yaml up --build
```

---

Analiz ve grafikleri oluşturmak için aşağıdaki komutlardan birini kullanabilirsiniz.

```
./run-analysis.sh
```

permission denied hatası almanız halinde <mark>chmod +x run-analysis.sh</mark> komutunu çalıştırınız.

veya

```
docker compose -f docker-compose.analysis.yaml up --build
```

Grafikler analysis klasörü altında oluşturulacaktır.

---
Projeyi ayağa kaldırdıktan sonra aşağıdaki adreslerden servislere erişebilirsiniz:

http://localhost:9411/zipkin/  adresinden zipkin arayüzüne erişebilirsiniz.\
1801, 1802, 1803, 1804 portlarından MQTT'ye erişebilirsiniz.
---

Gözlem sırasında elde edilen verile sql-dump klasörü altındadır.