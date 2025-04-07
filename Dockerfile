# Use CentOS 7 as the base image
FROM centos:7

# Fix CentOS 7 repository URLs
RUN sed -i 's|^mirrorlist=|#mirrorlist=|g' /etc/yum.repos.d/*.repo && \
    sed -i 's|^#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/*.repo

RUN yum upgrade -y && \
    yum -y install epel-release && \
    yum -y install httpd httpd-tools httpd-devel mod_wsgi \
      python2 python2-pip ca-certificates python2-certifi MySQL-python \
      python2-setuptools && \
    yum clean all

# intermediate PIP upgrade needed to get to modern pip
# then really upgrade PIP
RUN python -m pip install --upgrade "pip<21" "setuptools<45" "wheel" && \
    pip install --upgrade pip

# install python deps
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

RUN rm -rf /run/httpd/httpd.pid && \
    chmod 755 /run/httpd && \
    chown -R root:apache /var/log/httpd && \
    chmod 775 /var/log/httpd

# Set working directory
WORKDIR /var/www/django

# Copy Apache configuration
COPY httpd.conf /etc/httpd/conf/httpd.conf

# Ensure mime.types exists
RUN cp -f /usr/share/mime/packages/freedesktop.org.xml /etc/httpd/conf/mime.types

# Start Apache
CMD ["/usr/sbin/httpd", "-DFOREGROUND"]
