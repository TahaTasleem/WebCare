// Constants for all components
const HEIGHTEMSCALE = 1 * 1.75;
const WIDTHEMSCALE = 0.4 * 1.75;

var convertrowunittoem = (value) => {
    /* Convert Row Unit to EM */
    return applyscaling(value, true);
};

var convertcolunittoem = (value) => {
    /* Convert Col Unit to EM */
    return applyscaling(value, false);
};

var applyscaling = (value, height) => {
    /* apply scaling to value */
    var scaling;
    if (height) scaling = HEIGHTEMSCALE;
    else scaling = WIDTHEMSCALE;
    // round it to a single digit
    return (scaling * value).toFixed(1);
};

export { convertcolunittoem, convertrowunittoem };
