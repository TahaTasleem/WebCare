"use strict";

import React from "react";
import Prompt from "./prompt.js";
import Grid from "./grid.js";
import Button from "./button.js";
import Label from "./label.js";
import WDText from "./text.js";
import GroupBox from "./groupbox.js";
import { SchemeContext } from "./scheme.js";
import { convertcolunittoem, convertrowunittoem } from "./utils.js";
import { produce } from 'immer';
import { unstable_batchedUpdates } from 'react-dom';

class Screen extends React.PureComponent {
    constructor(props) {
        super(props);
        this.state = {
            prompts: this.props.prompts,
            grids: this.props.grids,
            buttons: this.props.buttons,
            texts: this.props.texts,
            groupboxes: this.props.groupboxes,
            scheme: {
                ...this.props.scheme,
                isgc: this.props.isgc
            },

        };
        this.gridrefs = [];
    }

    addPrompt = (prompt) => {
        this.setState((prevState) => {
            const tprompts = prevState.prompts.filter(
                (e) => e.name !== prompt.name
            );
            return {
                prompts: [...tprompts, prompt],
            };
        });
    };

    addButton = (button) => {
        this.setState((prevState) => {
            const tbuttons = prevState.buttons.filter(
                (e) => e.id !== button.id
            );
            return {
                buttons: [...tbuttons, button],
            };
        });
    };

    addText = (text) => {
        this.setState((prevState) => {
            const ttexts = prevState.texts.filter(
                (e) => e.id !== text.id
            );
            return {
                texts: [...ttexts, text],
            };
        });
    };

    addGrid = (grid) => {
        this.setState((prevState) => {
            const tgrids = prevState.grids.filter((e) => e.id !== grid.id);
            return {
                grids: [...tgrids, grid],
            };
        });
    };

    updateScheme = (schemeobj) => {
        this.setState((prevState) => {
            return produce(prevState, draft => {
                draft.scheme[schemeobj.area] = schemeobj;
            });
        });
    };

    // not sure if I need this
    removePrompt = (promptid) => {
        this.setState((prevState) => ({
            prompts: prevState.prompts.filter((e) => e.name !== promptid),
        }));
    };

    setValue = (ndx, value) => {
        //console.log("setValue", ndx, value);
        this.setState((prevState) =>
            produce(prevState, draft => {
                draft.prompts[ndx].value = value;
            })
        );
    };

    setValuefromHost = (targetid, value, bgcolour, textcolour) => {
        //console.log("setValue2", targetid, value);
        this.setState((prevState) => {
            const ndx = prevState.prompts.findIndex(
                (prompt) => prompt.name === targetid
            );
            return produce(prevState, draft => {
                draft.prompts[ndx] = {
                    ...draft.prompts[ndx],
                    value: value,
                    bgcolour: bgcolour,
                    textcolour: textcolour,
                };
            });
        });
    };

    setGridValue = (gridindex, row, col, value) => {
        //console.log("setGridValue", gridindex, row, col, value);
        this.setState((prevState) =>
            produce(prevState, draft => {
                draft.grids[gridindex].prompts[row][col].value = value;
            })
        );
    };

    // Batching state updates to reduce the number of re-renders
    // This function ensures that multiple updates are processed in a single render cycle.
    batchUpdate = (updateFunc) => {
        let updateQueue = [];
        return (...args) => {
            updateQueue.push(args);
            if (updateQueue.length === 1) {
                requestAnimationFrame(() => {
                    unstable_batchedUpdates(() => {
                        updateQueue.forEach((args) => updateFunc(...args));
                        updateQueue = [];
                    });
                });
            }
        };
    };

    setGridValuefromHost = this.batchUpdate((targetid, mvndx, value, bgcolour, textcolour) => {
        //console.log("setGridValue2", targetid, mvndx, value);
        const promptnum = targetid.split("_")[1];
        this.setState((prevState) => {
            const gridindex = prevState.grids.findIndex(
                (grid) =>
                    grid.startprompt <= promptnum && grid.endprompt >= promptnum
            );
            if (gridindex == -1) {
                console.log("couldn't find grid");
                return;
            }
            const grid = prevState.grids[gridindex];
            if (!Array.isArray(grid.prompts) || grid.prompts.length == 0) {
                console.log("No prompts defined in grid");
                return;
            }
            const promptndx = grid.prompts[0].findIndex(
                (prompt) =>
                    prompt.name.substring(0, prompt.name.length - 2) ===
                    targetid
            );
            if (promptndx == -1) {
                console.log("couldn't find prompt");
                return;
            }
            return produce(prevState, draft => {
                draft.grids[gridindex].prompts[mvndx - 1][promptndx] = {
                    ...draft.grids[gridindex].prompts[mvndx - 1][promptndx],
                    value: value,
                    bgcolour: bgcolour,
                    textcolour: textcolour,
                };
            });
        });
    });

    insertRowInGrid = (promptnum, mvndx) => {
        //console.log("insertRowInGrid", promptnum, mvndx);
        this.setState((prevState) => {
            const gridindex = prevState.grids.findIndex(
                (grid) =>
                    grid.startprompt <= promptnum && grid.endprompt >= promptnum
            );
            if (gridindex == -1) {
                console.log("couldn't find grid");
                return;
            }
            const grid = prevState.grids[gridindex];
            if (!Array.isArray(grid.prompts) || grid.prompts.length == 0) {
                console.log("No prompts defined in grid");
                return;
            }
            let rowToInsert = structuredClone(prevState.grids[gridindex].prompts[mvndx - 1]).map((prompt) => {
                prompt.value = "";
                return prompt;
            });

            return produce(prevState, draft => {
                draft.grids[gridindex].prompts = [
                    ...draft.grids[gridindex].prompts.slice(0, mvndx - 1),
                    rowToInsert,
                    ...draft.grids[gridindex].prompts.slice(mvndx - 1).map((row) => {
                        // Re-number all the rows
                        var rowCopy = row.map((prompt) => {
                            var splitname = prompt.name.split("_");
                            splitname[2] = parseInt(splitname[2]) + 1;
                            const rowpos = parseInt(prompt.rowpos) + 1;
                            return {
                                ...prompt,
                                name: splitname.join("_"),
                                rowpos: rowpos,
                            };
                        });
                        return rowCopy;
                    }),
                ];
            });
        });
    };

    deleteRowFromGrid = (promptnum, mvndx) => {
        //console.log("deleteRowFromGrid", promptnum, mvndx);
        this.setState((prevState) => {
            const gridindex = prevState.grids.findIndex(
                (grid) =>
                    grid.startprompt <= promptnum && grid.endprompt >= promptnum
            );
            if (gridindex == -1) {
                console.log("couldn't find grid");
                return;
            }
            const grid = prevState.grids[gridindex];
            if (!Array.isArray(grid.prompts) || grid.prompts.length == 0) {
                console.log("No prompts defined in grid");
                return;
            }
            var firstRow;
            if (mvndx == 1) {
                // Clone the second row's data into the first row
                // The first row is special and has all the additional properties, can't just remove it
                const rowTwo = structuredClone(prevState.grids[gridindex].prompts[1]);
                firstRow = structuredClone(prevState.grids[gridindex].prompts[0]).map((prompt, index) => {
                    return {
                        ...prompt,
                        value: rowTwo[index].value,
                        bgcolour: rowTwo[index].bgcolour,
                        textcolour: rowTwo[index].textcolour,
                    }
                });
                // Pretend we're deleting the second row
                mvndx = 2;
            } else {
                firstRow = prevState.grids[gridindex].prompts[0];
            }
            return produce(prevState, draft => {
                draft.grids[gridindex].prompts = [
                    firstRow,
                    ...draft.grids[gridindex].prompts.slice(1, mvndx - 1),
                    ...draft.grids[gridindex].prompts.slice(mvndx).map((row) => {
                        // Re-number all the rows
                        var rowCopy = row.map((prompt) => {
                            var splitname = prompt.name.split("_");
                            splitname[2] = parseInt(splitname[2]) - 1;
                            const rowpos = parseInt(prompt.rowpos) - 1;
                            return {
                                ...prompt,
                                name: splitname.join("_"),
                                rowpos: rowpos,
                            };
                        });
                        return rowCopy;
                    }),
                ];
            });
        });
    };

    scrollToGridItem = (focusprompt) => {
        const promptnum = parseInt(focusprompt);
        const row = parseInt(focusprompt.split(".")[1]);
        //console.log("scrollToGridItem", promptnum, row);
        const gridindex = this.state.grids.findIndex(
            (grid) =>
                grid.startprompt <= promptnum && grid.endprompt >= promptnum
        );

        this.gridrefs[gridindex].current.scrollToItem(row);
    };

    render() {
        let style = {};
        style.top =
            convertrowunittoem(this.props.startrowdraw + this.props.rowoffset) +
            "em";
        if (this.props.fillcontainer) {
            style.left = 0;
            style.right = 0;
            style.bottom = 0;
        } else if (this.props.position == "FULLSCREEN") {
            style.left = 0;
            style.right = 0;
            style.bottom = convertrowunittoem(1.6) + "em";
        } else {
            style.height = "calc(" + this.props.height + "em + 6px)";
            style.width = "calc(" + (this.props.width + 1) + "em + 6px)";
            style.left =
                convertcolunittoem(this.props.startcol + this.props.coloffset) +
                "em";
        }
        if (!this.props.draw) {
            style.display = "none";
        }
        style.backgroundColor = this.state.scheme?.BACKGROUND?.colour;
        style.color = this.state.scheme?.TEXT?.colour;
        let startcol = convertcolunittoem(
            this.props.startcol + this.props.coloffset
        );
        if (this.props.fillcontainer || this.props.position == "FULLSCREEN") {
            startcol = "0";
        }

        const screenprompts = this.state.prompts.map((prompt, index) => {
            let title = "";
            if (prompt.edittype != "PASSWORD") {
                title = prompt.value;
            }

            return (
                <Prompt
                    key={prompt.name}
                    index={index}
                    prompt={prompt}
                    left={
                        (
                            (100 *
                                convertcolunittoem(
                                    prompt.datacol - this.props.startcol
                                )) /
                            this.props.guiwidth
                        ).toFixed(2) + "%"
                    }
                    screenendrow={this.props.endrow}
                    screenguiwidth={this.props.guiwidth}
                    screenstartcol={this.props.startcol}
                    setValue={this.setValue}
                    title={title}
                    top={
                        convertrowunittoem(
                            prompt.datarow - this.props.startrow
                        ) + "em"
                    }
                    width={
                        (
                            (100 * convertcolunittoem(prompt.displaywidth)) /
                            this.props.guiwidth
                        ).toFixed(2) + "%"
                    }
                />
            );
        });

        const screengrids = this.state.grids.map((grid, index) => {
            let classnames = "grid";
            if (grid.verticallines == "Y") classnames += " verticalgrid";
            if (grid.horizontallines == "Y") classnames += " horizontalgrid";
            if (grid.small == "Y") classnames += " small";
            let isshowselect = false;
            if (
                grid.controltype == "" ||
                ["ES", "MES"].includes(grid.controltype)
            ) {
                classnames += " editgrid";
            }
            if (
                ["SS", "DS", "MSS", "MS", "ES", "MES"].includes(
                    grid.controltype
                )
            ) {
                classnames += " showselect";
                isshowselect = true;
            }
            if (["MSS", "MS", "MES"].includes(grid.controltype)) {
                classnames += " multiselect";
            }

            let otherlabels;
            if (grid.headingstyle == "F"){
                if (Array.isArray(grid.prompts) && grid.prompts.length > 0){
                    otherlabels = grid.prompts[0].map((prompt, index) => {
                        if (prompt.displaywidth > 0) {
                            return (
                                <Label
                                    key={index}
                                    grid={false}
                                    name={prompt.name}
                                    top={prompt.labeltop}
                                    left={prompt.labelleft}
                                    tag={prompt.labeltag}
                                />
                            );
                        }
                    });
                }
            }
            const gridref = React.createRef();
            this.gridrefs[index] = gridref;

            return (
                <span key={grid.id}>
                    <div
                        key={grid.id}
                        id={grid.id}
                        className={classnames}
                        style={{
                            top:
                                convertrowunittoem(
                                    grid.startrow - this.props.startrow
                                ) + "em",
                            left:
                                (
                                    (100 *
                                        convertcolunittoem(
                                            grid.startcol - this.props.startcol
                                        )) /
                                    this.props.guiwidth
                                ).toFixed(2) + "%",
                            height:
                                convertrowunittoem(
                                    grid.endrow - grid.startrow + 0.925
                                ) + "em",
                            width:
                                (
                                    (100 *
                                        convertcolunittoem(
                                            grid.endcol - grid.startcol + 1.1
                                        )) /
                                    this.props.guiwidth
                                ).toFixed(2) + "%",
                            backgroundColor: this.state.scheme?.EDITABLE?.colour,
                        }}
                    >
                        <Grid
                            ref={gridref}
                            setValue={this.setGridValue}
                            grid={grid}
                            screenendrow={this.props.endrow}
                            gridindex={index}
                        />
                    </div>
                    {otherlabels}
                </span>
            );
        });

        const autobuttons = this.state.buttons.map((button, index) => {
            if (button.autoposition)
                return <Button key={button.id} index={index} button={button} />;
        });

        const otherbuttons = this.state.buttons.map((button, index) => {
            if (!button.autoposition)
                return <Button key={button.id} index={index} button={button} />;
        });

        const screentexts = this.state.texts.map((text, index) => {
            if (!text.heading)
                return <WDText key={text.id} index={index} text={text} />;
        });

        const screenheadings = this.state.texts.map((text, index) => {
            if (text.heading)
                return <WDText key={text.id} index={index} text={text} />;
        });
        const groupboxes = this.state.groupboxes.map((groupbox, index) => {
            return <GroupBox key={groupbox.id} index={index} groupbox={groupbox} />
         });
        return (
            <div
                className="reactscreen"
                id={this.props.screenid + "_screen"}
                data-screenid={this.props.screenid}
                data-focuspromptid={
                    this.props.focuspromptnum
                        ? this.props.screenid + "_" + this.props.focuspromptnum
                        : ""
                }
                style={style}
                data-fillcontainer={this.props.fillcontainer}
                data-startrow={convertrowunittoem(
                    this.props.startrowdraw + this.props.rowoffset
                )}
                data-startcol={startcol}
                data-endrow={this.props.endrow}
                data-position={this.props.position}
            >
                <div className="subscreen">
                    <SchemeContext.Provider value={this.state.scheme}>
                    {!this.props.fillcontainer && (
                        <button
                            type="button"
                            className="close"
                            aria-label="Close"
                            onClick={() => WD.input(WD.ESCAPE + "F4", true)}
                        >
                            <span aria-hidden="true">&times;</span>
                        </button>
                    )}
                    {this.props.position == "FULLSCREEN" ? (
                        <div
                            className="scrollable"
                            style={{ top: !this.props.hasheading ? 0 : "" }}
                        >
                            {groupboxes}
                            {screenprompts}
                            {screengrids}
                            {otherbuttons}
                            {screentexts}
                        </div>
                    ) : (
                        <>
                            {groupboxes}
                            {screenprompts}
                            {screengrids}
                            {otherbuttons}
                            {screentexts}
                        </>
                    )}
                    {screenheadings}
                    {autobuttons}
                    </SchemeContext.Provider>
                </div>
            </div>
        );
    }
}

export default Screen;
