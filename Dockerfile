FROM sagemath/sagemath
MAINTAINER Academic Systems

# change user from sage to root

USER root

# update, upgrade, & install packages

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y lighttpd python-pip wget

# configure lighttpd

COPY assets/lighttpd.conf /etc/lighttpd/lighttpd.conf
RUN touch /var/log/lighttpd/error.log
RUN chmod 664 /var/log/lighttpd/error.log
RUN chown -R sage:sage /var/log/lighttpd
RUN rm -rf /var/www/html

# configure web.py server

RUN wget https://www.saddi.com/software/flup/dist/flup-1.0.2.tar.gz
RUN tar xzf flup-1.0.2.tar.gz && rm flup-1.0.2.tar.gz
RUN cd flup-1.0.2 && sage --python setup.py install && cd ..

RUN wget http://webpy.org/static/web.py-0.38.tar.gz
RUN tar xzf web.py-0.38.tar.gz && rm web.py-0.38.tar.gz
RUN cd web.py-0.38 && sage --python setup.py install && cd ..

COPY assets/sageserver.py /var/www/sageserver.py

RUN chown sage:sage /var/www/sageserver.py && chown sage:sage /var/www
RUN chmod 555 /var/www/sageserver.py

CMD ["lighttpd", "-D", "-f", "/etc/lighttpd/lighttpd.conf"]

