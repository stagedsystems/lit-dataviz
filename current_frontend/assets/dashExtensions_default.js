//this is the version that leaflet directly is calling!

window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {  
        zoneStyle: function(feature, context) { //note - data on single feature
            const {
                //classes,
                colorscale,
                style,
                colorProp,
                selectedZones,
                min,
                max,
            } = context.props.hideout; // get props from hideout

            //fill style
            // const value = feature.properties[colorProp]; // get value the determines the color
            // for (let i = 0; i < classes.length; ++i) {
            //     if (value > classes[i]) {
            //         style.fillColor = colorscale[i]; // set the fill color according to the class
            //     }
            // }
            
            //attempt to recreate logic using chroma https://gka.github.io/chroma.js/
            const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
            style.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop.
         



            //
            //outline style for selected polys
           // const selectedZones = feature.properties.fiberhood;
           const selected = selectedZones.includes(feature.properties.fiberhood);
           if(selected){
                style.color="blue";
                style.dashArray='';
                style.weight=5;
            }
           else{
                style.color="gray";
                style.dashArray='3';
                style.weight=2;
        
            }
  

            return style;
        },
        cabinetPointToLayer: function(feature, latlng, context){
            //const chroma = ; //attempt to add this here
            const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
            const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
            circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop.
            return L.circleMarker(latlng, circleOptions);  // sender a simple circle marker.
        },      
        pointToLayer: function(feature, latlng, context){
            //const chroma = ; //attempt to add this here
            const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
            const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
            circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop.
            return L.circleMarker(latlng, circleOptions);  // sender a simple circle marker.
        },      
        edgeColorByStatus: function(feature, context) {
            const {                
                style,
                colorProp
            } = context.props.hideout; // get props from hideout
            const value = feature.properties[colorProp]; // get value the determines the color
            if (value == "Construction Complete"){
                style.color = "green";
            }   else if (value == "Active Construction"){
                style.color = "yellow";
            }else{            
                style.color = "black";
            }
            return style;
        }
      
    }

});