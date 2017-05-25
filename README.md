CupsMQ aims to provide cups backends, frontends, configuration and monitoring mechanisms to use cups
as a message queue.

planned work:

- provide active ftp backend (backend sends file to ftp server)
- provide passive ftp frontend (ftp server that gives files to cups queues after recieval)
  - thus implementing pyftplib AbstractedFS subclass mapping existing cups queues to a virtual 
    filesystem in FTPD (low priority but highly interesting ;) )
- reverse the above (add active ftp frontend and passive backend)

- subsequently add passive and active backends and frontends for various other protocols
