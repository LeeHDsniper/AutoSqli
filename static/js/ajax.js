var xmlhttp;
function loadXMLDocByGet(url,cfunc)                                               //AJAX-----使用GET方式
{    
    if(window.XMLHttpRequest)
        xmlhttp=new XMLHttpRequest();
    else
        xmlhttp=new ActiveXObject("Microslft.XMLHTTP");  
    xmlhttp.onreadystatechange=cfunc;
    xmlhttp.open("GET",url,true);
    xmlhttp.send();
}
function loadXMLDocByPost(send_content,url,cfunc)                   //AJAX-----使用POST方式
{
    if(window.XMLHttpRequest)
        xmlhttp=new XMLHttpRequest();
    else
        xmlhttp=new ActiveXObject("Microslft.XMLHTTP");  
    xmlhttp.onreadystatechange=cfunc;
    xmlhttp.open("POST",url,true);
    xmlhttp.setRequestHeader("Content-type","application/json");
    xmlhttp.send(send_content);
}
