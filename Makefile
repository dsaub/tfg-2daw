docker:
	docker build -t ghcr.io/dsaub/proyecto-mvc:development .
	docker push ghcr.io/dsaub/proyecto-mvc:development

test:
	./manage.py test