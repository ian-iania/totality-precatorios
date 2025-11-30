/** Script responsvel pela integrao de outros sistemas com o portalDeServios..

*/
function aplicarEstiloIntegracao(){    
            document.writeln('<link rel="stylesheet" type="text/css" href="http://www.tjrj.jus.br/css/integracaoPortal.css"/>');      
}

 
try{
  topo = top;
		if((topo.location.pathname.indexOf ('portalDeServicos') != -1) || (top.location.pathname.indexOf ('portaldesistemas') != -1)){
        aplicarEstiloIntegracao()

    }

}

catch(Ex){
        aplicarEstiloIntegracao()

}


 

 
