"use strict";

import React, {  useState, useEffect, useCallback, memo, useImperativeHandle } from "react";
import memoize from "memoize-one";
import { VariableSizeList as List, areEqual } from "react-window";
import AutoSizer from "react-virtualized-auto-sizer";
import Prompt from "./prompt.js";
import Label from "./label.js";
import { useContext } from "react";
import { SchemeContext } from "./scheme.js";

const Row = memo(function ARow(props) {
    // Data passed to List as "itemData" is available as props.data
    const { grid, extraprops, setValue } = props.data;
    const gridindex = extraprops.gridindex;
    const row = grid.prompts[props.index];
    const scheme = useContext(SchemeContext);

    const onclick = (e) => {
        //console.log("row click", e.currentTarget);

        if (grid.controltype == "SS" || grid.controltype == "ES") {
            WD.ssclick(e.currentTarget, props.index + 1, false, true);
        } else if (grid.controltype == "MSS") {
            WD.ssclick(e.currentTarget, props.index + 1, false, false);
        } else if (grid.controltype == "DS") {
            WD.ssclick(e.currentTarget, props.index + 1, true, true);
        } else if (grid.controltype == "MS") {
            WD.ssclick(e.currentTarget, props.index + 1, false, false);
        }
    };
    const ondblclick = (e) => {
        //console.log("row double click", e.currentTarget);

        if (grid.controltype == "SS" || grid.controltype == "ES") {
            WD.ssdblclick(e.currentTarget, props.index + 1, true, true);
        } else if (grid.controltype == "MSS") {
            WD.ssdblclick(e.currentTarget, props.index + 1, true, true);
        }
    };

    let classnames = "gridrow";
    let rowcolour;
    if (grid.controltype == "SS" || grid.controltype == "ES" ||
        grid.controltype == "MSS" || grid.controltype == "DS" || grid.controltype == "MS") {
        classnames += " selectgrid";
        rowcolour = scheme?.EDITABLE?.colour;
    } else if (grid.controltype == "DS") {
        classnames += " singleselect";
        rowcolour = scheme?.EDITABLE?.colour;
    }
    if (props.index % 2) {
        rowcolour = 'rgba(0,0,0,0.06)';
    }
    return (
        <tr
            data-promptno={grid.startprompt}
            onClick={(e) => onclick(e)}
            onDoubleClick={(e) => ondblclick(e)}
            style={{ ...props.style, backgroundColor: rowcolour }}
            className={classnames}
        >
            {row.map((prompt, colndx) => (
                <td
                    key={colndx}
                    style={{
                        left: grid.freezecol - 1 >= colndx
                            ? grid.headers[colndx].newwidth
                            : undefined,
                        width: grid.prompts[0][colndx].width,
                        maxWidth: grid.prompts[0][colndx].width,
                        minWidth: grid.prompts[0][colndx].width,
                        backgroundColor: prompt.bgcolour,
                        color: "#FFF"
                    }}
                    className={`
                        ${grid.freezecol - 1 >= colndx ? "freezecol" : ""}
                        ${grid.freezecol - 1 == colndx ? "lastfreezecol" : ""}
                        `}
                >
                    <Prompt
                        key={prompt.name}
                        col={colndx}
                        prompt={{ ...grid.prompts[0][colndx], ...prompt }}
                        grid={true}
                        gridfocus1={grid.gridfocus1}
                        gridfocus2={grid.gridfocus2}
                        gridcontrol={grid.controltype}
                        gridindex={gridindex}
                        row={props.index}
                        screenendrow={extraprops.screenendrow}
                        setValue={setValue}
                    />
                </td>
            ))
            }
        </tr>
    )
}, areEqual);
const createItemData = memoize((grid, extraprops, setValue) => ({
    grid,
    extraprops,
    setValue,
}));

const DataGrid = React.forwardRef((props, ref) => {
    const itemData = createItemData(
        props.grid,
        props.extraprops,
        props.setValue
    );
    const hasHeader =
        props.grid.headingstyle !== "F" && props.grid.headingstyle !== "N";
    const listRef = React.useRef();
    const scheme = useContext(SchemeContext);

    const [windowWidth, setWindowWidth] = useState(window.innerWidth - 41);
    
    useImperativeHandle(ref, () => ({
        scrollToItem,
    }));

    const scrollToItem = (row) => {
        listRef.current.scrollToItem(row);
    };

    const handleResize = useCallback(() => {
        setWindowWidth(window.innerWidth - 41);
      }, []);

    useEffect(() => {
        window.addEventListener('resize', handleResize);
        return () => {
            window.removeEventListener('resize', handleResize);
        };
      }, [handleResize]);
    
    useEffect(() => {
        listRef.current?.resetAfterIndex(0);
    }, [windowWidth]);

    const getLongestWord = (decodedString) => {
        const words = decodedString.split(" ");
        return words.reduce((maxLength, word) => {
            return Math.max(maxLength, word.length);
        }, 0);
    };
    
    const getItemSize = (index) => {
        const characterWidth = 8; 
        let requiredRows = 1;

        const gridwidth = parseFloat(props.grid.width);
        const effectiveGridWidth = (gridwidth / 100) * windowWidth;
        props.grid.prompts[index].map((prompt, colndx) => {
            prompt = { ...props.grid.prompts[0][colndx], ...prompt };
            if (prompt.edittype === "WP" || prompt.edittype === "WORDWRAP" || prompt.edittype === "SCH.SCHEDULE") {
                if (prompt.prompttype === "S") {
                    const contentLength = prompt.value ? prompt.value.length : 0;
                    const longestWord = getLongestWord(decodeURIComponent(prompt.value));
                    const promptWidthPercentage = parseFloat(prompt.width);
                    const promptWidthPixels = (promptWidthPercentage / 100) * effectiveGridWidth;
                    const charsPerRow = promptWidthPixels / characterWidth;
                    const tRequiredRows = Math.ceil(contentLength / charsPerRow) + Math.floor(longestWord / charsPerRow);
                    requiredRows = Math.max(requiredRows, tRequiredRows);
                } else {
                    requiredRows = Math.max(requiredRows, prompt.numrows);
                }
            }
        });
        return 8 + Math.floor(14.5 * requiredRows);
    };
    return (
        <table>
            {hasHeader && (
                <thead style={{ backgroundColor: scheme?.BACKGROUND?.colour }}>
                    <tr>
                        {props.grid.headers
                            .map((header, index, headers) => {
                                const previousWidth = headers[index].newwidth;
                                return ( header.width > 0 &&
                                    <th
                                        className={`
                                        ${props.grid.freezecol - 1 >= index ? "freezecol" : ""}
                                        ${props.grid.freezecol - 1 == index ? "lastfreezecol" : ""}
                                    `}
                                        style={{
                                            left: props.grid.freezecol - 1 >= index
                                                ? index == 0
                                                    ? '0'
                                                    : `calc(${previousWidth} - 3px)`
                                                : undefined,
                                            width: header.width + "%", maxWidth: header.width + "%"
                                        }}
                                        colSpan={1}
                                        key={index}
                                    >
                                        <Label tag={decodeURIComponent(header.tag)} />
                                    </th>
                                )
                            })
                        }
                    </tr>
                </thead>
            )}
            <tbody>
                <AutoSizer>
                    {({ height, width }) => (
                        <List
                            ref={listRef}
                            height={height - 2}
                            itemCount={props.grid.prompts.length}
                            itemData={itemData}
                            itemSize={getItemSize}
                            overscanCount={
                                Math.ceil(props.grid.endrow - props.grid.startrow)
                            }
                            width={width - 3}
                        >
                            {Row}
                        </List>
                    )}
                </AutoSizer>
            </tbody>
        </table>
    );
});
DataGrid.displayName = "DataGrid";

const Grid = React.forwardRef((props, myref) => {
    const extraprops = {
        gridindex: props.gridindex,
        screenendrow: props.screenendrow,
    };
    const gridref = React.useRef();

    useImperativeHandle(myref, () => ({
        scrollToItem,
    }));

    function scrollToItem(row) {
        gridref.current.scrollToItem(row);
    }

    return (
        <DataGrid
            ref={gridref}
            extraprops={extraprops}
            grid={props.grid}
            setValue={props.setValue}
        />
    );
});
Grid.displayName = "Grid";

export default Grid;
