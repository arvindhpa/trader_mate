# Ran in EC2 container with TA LIB, BINANCE Keys

Step-By-Step Instructions: (Need to type only the ec2 lines)
$ ssh -i /e/LINUX/OutReal/trader.pem ec2-user@ec2-13-40-54-199.eu-west-2.compute.amazonaws.com

[ec2-user@ip-172-31-21-195 ~]$ wget https://github.com/TA-Lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz
[ec2-user@ip-172-31-21-195 ~]$ ls
ta-lib-0.6.4-src.tar.gz
[ec2-user@ip-172-31-21-195 ~]$ ls -l ta-lib-0.6.4-src.tar.gz
-rw-r--r--. 1 ec2-user ec2-user 946924 Jan 11 04:59 ta-lib-0.6.4-src.tar.gz
[ec2-user@ip-172-31-21-195 ~]$ tar -xzf ta-lib-0.6.4-src.tar.gz
[ec2-user@ip-172-31-21-195 ~]$ ls
ta-lib-0.6.4  ta-lib-0.6.4-src.tar.gz
[ec2-user@ip-172-31-21-195 ~]$ cd ta-lib-0.6.4
[ec2-user@ip-172-31-21-195 ta-lib-0.6.4]$ ls
Makefile.am  VERSION     compile       configure     include     m4       ta-lib.dpkg.in
Makefile.in  aclocal.m4  config.guess  configure.ac  install-sh  missing  ta-lib.pc.in
README.md    ar-lib      config.sub    depcomp       ltmain.sh   src      ta-lib.spec.in
[ec2-user@ip-172-31-21-195 ta-lib-0.6.4]$ cat README.md
[ec2-user@ip-172-31-21-195 ta-lib-0.6.4]$ ls src
Makefile.am  Makefile.in  ta_abstract  ta_common  ta_func  tools
[ec2-user@ip-172-31-21-195 ta-lib-0.6.4]$ ./configure --prefix=/usr
[ec2-user@ip-172-31-21-195 ta-lib-0.6.4]$ make
[ec2-user@ip-172-31-21-195 ta-lib-0.6.4]$ ta-lib-config --version
0.4.0
[ec2-user@ip-172-31-21-195 ta-lib-0.6.4]$ cd ..
[ec2-user@ip-172-31-21-195 ~]$ ls
ta-lib-0.6.4  ta-lib-0.6.4-src.tar.gz
[ec2-user@ip-172-31-21-195 ~]$ rm -rf ta-lib-0.6
[ec2-user@ip-172-31-21-195 ~]$ ls
ta-lib-0.6.4  ta-lib-0.6.4-src.tar.gz
[ec2-user@ip-172-31-21-195 ~]$ rm -rf ta-lib-0.6.4
[ec2-user@ip-172-31-21-195 ~]$ ls
[ec2-user@ip-172-31-21-195 ~]$ python3 --version
Python 3.9.20
[ec2-user@ip-172-31-21-195 ~]$ nano test_talib.py
[ec2-user@ip-172-31-21-195 ~]$ python3 test_talib.py
[ec2-user@ip-172-31-21-195 ~]$ pip3 install TA-Lib
[ec2-user@ip-172-31-21-195 ~]$ python3
>>> import talib
>>> print(talib.get_functions())
