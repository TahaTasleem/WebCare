// WebDirect Javascript
// @author: bouchcla
//

// WebDirect Namespace
var WD = function() {
    var lockResolver;
    var terminal = null;
    var connected = false;
    var itemqueue = [];
    var browsers = {};
    var dirtydata = null;
    var dirtydataprompt = 0;
    var sentdata = false;
    var idletimerid = 0;
    var MAX_TCL_IDLE_TIME = 20000; // 20 seconds
    var keepTCLhidden = true;
    var hostfocusprompt = -1;
    var mainwindow = false;
    var selfreload = false;
    var loggedout = true;
    var connecting = false;
    var screensdisabled = false;
    var wcontainer = $("#windowcontainer");
    var schemesettings = {};
    var editor = null;
    var diffnav = null;
    var clicktimer = null;
    var alttab = false;
    var searching = false;
    var isgc = $("body").hasClass("gc");
    var tclcols = 80;
    var tclrows = 24;
    var socket = null;
    var socketManager = null;
    var disconnected = null;
    var autoconnect = false;
    var clickqueue = [];
    var screens = [];
    var reconnectTimer = null;
    var languageObject = {};
    var renderdataqueue = {};
    var waitingclasstimeoutid = null;
    var globaltoasttimeout;
    var itemqueueprocessed = true;
    var previousfocusinput = null;

    function isdisplayed(index, item) {
        return item.style.display != "none";
    }

    function inputhistory(input) {
        input.history = [];
        input.history.push("");
        var i = 0;
        input.on("keydown", function(e) {
            var key = e.which;
            switch (key) {
                case 13: // Enter
                    if (input.val() != "") {
                        i = input.history.length;
                        input.history[i - 1] = input.val();
                        input.history.push("");
                        if (input.history[i - 1] == input.history[i - 2]) {
                            input.history.splice(-2, 1);
                            i--;
                        }
                    }
                    return;
                case 38: // Up
                case 40: // Down
                    input.history[i] = input.val();
                    if (key == 38 && i != 0) {
                        i--;
                    } else if (key == 40 && i < input.history.length - 1) {
                        i++;
                    }
                    input.val(input.history[i]);
                    break;

                default:
                    return;
            }
            e.preventDefault();
        });
    }

    function fixObjectHeight(oScroll, oWnd, oSiblings, extraHeight) {
        // get height of our "siblings" we care about
        var height = 0;
        oSiblings.each(function() {
            height += Math.round($(this).outerHeight(true));
        });
        if (extraHeight !== undefined && extraHeight !== null) {
            height += extraHeight;
        }
        var sizeOfWindow = 0;
        // find our window size
        if (oWnd === window) {
            sizeOfWindow = $(oWnd).height() - height;
        } else {
            sizeOfWindow = oWnd.clientHeight - height;
        }
        // subtract our outer window size
        sizeOfWindow -= (oScroll.outerHeight(true) - oScroll.height()) + 10;
        oScroll.css("height", sizeOfWindow + "px");
    }

    function addWindowListener() {
        window.addEventListener("message", WD.receiveMessage, false);
    }

    function setupTerminal() {
        // Terminal Window Setup
        terminal = new Terminal();
        var tdom = $("#output");
        tdom.css({
            width: "100%"
        });
        terminal.open(tdom.get(0));
        terminal.onData(handleterminaldata);
        // Stop parent div from setting focus back to input box when terminal clicked
        tdom.on("click", function(event) {
            event.stopPropagation();
        });
        $("#tcl").find(".modal").on("click", function() {
            WD.hidetcl();
        });
        $("#tcl").find(".modal-dialog").on("click", function() {
            event.stopPropagation();
        });
        inputhistory($("#tclinput"));
    }

    function setTerminalSize() {
        // should we track terminal size from host
        terminal.resize(tclcols, tclrows);
    }

    function handleterminaldata(data) {
        // handle terminal data
        if (data.length == 1 && data.charCodeAt(0) == 127) {
            // Fix for backspace key
            data = "\b";
        }
        WD.input(data, null, null, true);
    }

    var popupBlockerChecker = {
        check: function(popup_window) {
            var _scope = this;
            if (popup_window) {
                if (/chrome/.test(navigator.userAgent.toLowerCase())) {
                    setTimeout(function() {
                        _scope._is_popup_blocked(_scope, popup_window);
                    }, 200);
                } else {
                    popup_window.onload = function() {
                        _scope._is_popup_blocked(_scope, popup_window);
                    };
                }
            } else {
                _scope._displayError();
            }
        },
        _is_popup_blocked: function(scope, popup_window) {
            if ((popup_window.innerHeight > 0) == false) {
                setCookie("popupcheck", "false", 14);
                scope._displayError();
            } else {
                setCookie("popupcheck", "true", 9999);
                popup_window.close();
            }
        },
        _displayError: function() {
            displayPopupWarning();
        }
    };

    function displayPopupWarning() {
        var appName = "WebDirect";
        if (isgc) {
            appName = "CloudCare";
        }

        setTimeout(function() {

            var WARNING_HEADER = WD.loadstringliteral("IDS_ERROR0079").toUpperCase();
            var WARNING_MESSAGE = WD.loadstringliteral("IDS_WEBWARN0001");
    
            WD.displaytoast({
                msg: ("<h2 style='text-align:center'>" + WARNING_HEADER + "<br/>" + WARNING_MESSAGE + ".</h2>").replace("<appName>", appName),
                msgtype: "ERROR"
            });

        }, 100);
    }

    function getiframe(targetid, contents) {
        var iframe = $("#" + jQueryID(targetid));
        if (iframe.length > 0) {
            if (iframe.is("div")) {
                iframe = iframe.find("iframe");
            }
        } else {
            // could be an external browser
            if (targetid in browsers) {
                iframe = $(browsers[targetid].document.getElementById("externalsource"));
            }
        }
        if (iframe && iframe.length && contents) {
            iframe = iframe.contents();
        }
        return iframe;
    }
    // Setup Login fields
    function setupLogin() {
        if ($('#login').length == 0) return;

        var overrides = false;
        if (wdserveroverride != "") {
            overrides = true;
        }

        var lastServer = getCookie("server");
        var $serverElement = $("#server");
        if (wdserveroverride != "") {
            $serverElement.val(wdserveroverride);
        } else if (lastServer != "" && $serverElement.is(":visible")) {
            $serverElement.val(lastServer);
        }
        if (!$serverElement.val()) {
            $serverElement.val($serverElement.children().first().val());
        }

        // This can't be last
        // and if first, need to call ".change()" on #server after changing its
        // val()
        $(document).on("change", "#server", WD.onServerChange);
        $serverElement.trigger("change");

        // Enable server prompt if more than one choice, else disable
        if ($serverElement.children().length <= 1 && $serverElement.prop("nodeName").toUpperCase() == "SELECT") {
            $serverElement.prop("disabled", true);
        } else {
            $serverElement.prop("disabled", false);
        }

        var account = getCookie("account");
        var $accountElement = $("#account");
        if (wdaccountoverride != "") {
            $accountElement.val(wdaccountoverride);
        } else if (account != "" && $accountElement.is(":visible")) {
            $accountElement.val(account);
        }
        if (!$accountElement.val()) {
            $accountElement.val($accountElement.children().first().val());
        }
    }
    /*
     * Checks to see if a supported browser is being used and, if not, displays a message
     */
    function checkBrowser() {
        if (!bowser.chrome && !bowser.msedge && !bowser.chromium) {
            // bowser.name + " " + bowser.version + ": Is IE? " + bowser.msie);
            var BROWSER_ERR = WD.loadstringliteral("IDS_WEBERR0005", "You are using an unsupported browser!  Please switch to Chrome or MS Edge (Chromium based).");
            WD.showmessage({
                msg: BROWSER_ERR,
                msgtype: "ERROR",
                button: [{
                    buttonlabel: "OK",
                    nosend: true
                }],
                header: WD.loadstringliteral("IDS_ERROR0022"),
                image: "wdres/exclamation.svg"
            });
        }
        var popupcheck = getCookie("popupcheck");
        if (popupcheck != "true") {
            var popup = window.open("static/blank.html", '_blank');
            popupBlockerChecker.check(popup);
        }
    }
    // Setup Editor
    function setupEditor() {
        require.config({
            paths: {
                'vs': approot + 'static/monaco-editor/min/vs'
            }
        });
        require(['vs/editor/editor.main'], function() {
            /**
             * Load custom SG/SX/Pick editor
             * https://microsoft.github.io/monaco-editor/playground.html#extending-language-services-custom-languages
             * view-source:https://microsoft.github.io/monaco-editor/monarch.html
             */
            monaco.languages.register({
                id: "sgx",
                extensions: [".sgx"],
                aliases: ["SGSX", "PickBASIC"],
                mimetypes: ["text/x.sgx"]
            });
            $.get(approot + "static/editor-languages/sgx.js", function(data) {
                var def = eval("(function(){ " + data + "; })()");
                monaco.languages.setMonarchTokensProvider("sgx", def);
                monaco.languages.setLanguageConfiguration("sgx", {
                    comments: {
                        lineComment: "*"
                    }
                });
            }, "text");

            // Build list of languages and populate picker
            var MODES = (function() {
                var modesIds = monaco.languages.getLanguages().map(function(lang) {
                    return lang.id;
                });
                modesIds.sort();

                return modesIds.map(function(modeId) {
                    return {
                        modeId: modeId,
                        sampleURL: 'index/samples/sample.' + modeId + '.txt'
                    };
                });
            })();
            var $lp = $("#language-picker");
            for (var i = 0; i < MODES.length; i++) {
                var o = document.createElement('option');
                o.textContent = MODES[i].modeId;
                $lp.append(o);
            }
            $lp.on("change", setEditorLanguage);
            $("#wdeditcancel").on("click", cancelEditor);
            $("#wdeditsave").on("click", saveEditor);
            // Update Theme
            var $tp = $("#theme-picker");
            var savedTheme = getCookie("edtheme");
            if (savedTheme) $tp.val(savedTheme);
            $tp.on("change", function() {
                //console.log($tp.get(0));
                var currentTheme = $tp.get(0).options[$tp.get(0).selectedIndex].value;
                setCookie("edtheme", $tp.val(), 30);
                monaco.editor.setTheme(currentTheme);
            });
            $('#inline-diff').on("change", function() {
                var bSideBySide = !$(this).is(':checked');
                editor.updateOptions({
                    renderSideBySide: bSideBySide
                });
                setCookie("edsbs", bSideBySide, 30);
            });
        });
    }
    // Change Editor Settings
    function updateEditorSettings() {
        //editor.updateOptions({
        //    lineNumbers: true
        //});
    }
    /**
     * Shows the Editor
     */
    function showEditor() {
        hotkeys.setScope("editor");
        $("#editorcontainer").show();
        // flip cursor to ready
        WD.ready();
    }
    /**
     * Hides the Editor
     */
    function hideEditor() {
        $("#editorcontainer").hide();
    }
    /**
     * Sets the language of the file being editted
     */
    function setEditorLanguage() {
        var $lang = $("#language-picker :selected");
        var myModel = editor.getModel();
        if (myModel.original) {
            monaco.editor.setModelLanguage(myModel.original, $lang.text());
            monaco.editor.setModelLanguage(myModel.modified, $lang.text());
        } else {
            monaco.editor.setModelLanguage(myModel, $lang.text());
        }
    }
    /**
     * Cancels the editting of the current file
     */
    function cancelEditor() {
        hideEditor();
        clearEditor();
        // Send some command back to terminate editing
        WD.input(WD.ESCAPE + "WHIR:WDEC" + WD.VM + "CANCEL", true);
    }
    /**
     * Clear Editor and its model(s)
     */
    function clearEditor() {
        var index, len;
        var models;
        if (editor) {
            if (editor.getModels) {
                models = editor.getModels();
                for (index = 0, len = models.length; index < len; index++) {
                    // console.log("Disposing editor model # " + index.toString());
                    models[index].dispose();
                }
            } else if (editor.getModel) {
                var myModel = editor.getModel();
                if (myModel) {
                    if (myModel.original) {
                        // console.log("Disposing diff models");
                        myModel.original.dispose();
                        if (myModel.modified) {
                            myModel.modified.dispose();
                        }
                        if (diffnav) {
                            diffnav.dispose();
                            diffnav = null;
                        }
                    } else {
                        // console.log("Disposing editor model");
                        myModel.dispose();
                    }
                }
            }
            editor.dispose();
            editor = null;
        }
        var $container = $('#editfilecontainer');
        if ($container.data("oldtitle")) {
            document.title = $container.data("oldtitle");
            $container.removeData("oldtitle");
            $("#editorlabel").html("");
        }
    }
    /**
     * Called when Editting fails for some reason
     */
    function failEditor() {
        hideEditor();
        WD.input(WD.ESCAPE + "WHIR:WDEC" + WD.VM + "FAIL-GEN", true);
    }
    /**
     * Callback for xhr (XML HTTP Request)
     * @callback xhrCallback
     * @param {string} error
     * @param {string} data
     */
    /**
     * XML HTTP Request
     * @param {string} url
     * @param {string} reqtype Request type (GET, POST, PUT, etc.)
     * @param {string} outdata Data to be sent (on POST, PUT, etc.)
     * @param {xhrCallback} cb callback
     */
    function xhr(url, reqtype, outdata, cb) {
        $.ajax({
            type: reqtype,
            url: url,
            dataType: 'text',
            data: outdata,
            processData: false,
            contentType: "text/plain",
            error: function(jqXHR, textStatus, errorThrown) {
                cb(jqXHR, this, null);
            }
        }).done(function(data, textStatus, jqXHR) {
            cb(jqXHR, null, data);
        });
    }

    /**
     * Load Editor content
     * @param {string} uri - uri to source
     * @param {string} language - Force code language used
     * @param {boolean} readonly - Whether the document is readonly or not
     */
    function loadEditorContent(uri, language, readonly) {
        xhr(approot + sid + "/edit/" + uri, "GET", "", function(jqXHR, err, data) {
            var $container = $('#editfilecontainer');

            clearEditor();

            if (err) {
                console.error(err);
                hideEditor();
                return;
            }

            if (!editor) {
                $container.empty();
                showEditor();
                var $tp = $("#theme-picker");
                var currentTheme = $tp.get(0).options[$tp.get(0).selectedIndex].value;
                editor = monaco.editor.create($container.get(0), {
                    model: null,
                    theme: currentTheme,
                    readOnly: readonly,
                    wordBasedSuggestions: false
                    //                     quickSuggestions: false
                });
            }

            // Create model
            var oldModel = editor.getModel();
            var newModel = monaco.editor.createModel(data, language, monaco.Uri.file(uri));
            editor.setModel(newModel);
            if (oldModel) {
                oldModel.dispose();
            }

            // add uppser and case shortcuts (CTRL-SHIFT-U/S)
            editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KEY_U, function() {
                editor.trigger("anystring", "editor.action.transformToUppercase");
            });
            editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KEY_L, function() {
                editor.trigger("anystring", "editor.action.transformToLowercase");
            });

            var $lp = $("#language-picker");
            $lp.get(0).value = editor.getModel().getModeId();
            $('#inline-diff').parent().addClass("hidden");
            $('#diffnavprev').parent().addClass("hidden");

            // Update page title / browser tab caption, if editing in main session (not a pop-up tab)
            if (!readonly) {
                $container.data("oldtitle", document.title);
                document.title = 'Editing "' + uri.split("\\").slice(-1)[0].split("/").slice(-1)[0] + '"';
                $("#editorlabel").html(document.title);
            }

            $container.data("uri", sid + "/edit/" + uri);

            editor.focus();
        });
    }

    /**
     * Load Diff Editor content
     * @param {string} uriOrig - URI to original copy of file (old)
     * @param {string} uriMod - URI to modified copy of file (new)
     * @param {string} language - Force source language used
     */
    function loadDiffEditorContent(uriOrig, uriMod, language) {
        var dataOrig = "";
        var dataMod = "";

        if (uriOrig == uriMod) {
            clearEditor();
            var msgError = WD.loadstringliteral("IDS_WEB0001", "Filenames are identical");
            WD.showmessage({
                msg: msgError,
                msgtype: "INFO",
                button: [{
                    buttonlabel: WD.loadstringliteral("IDS_CAP0067"),
                    nosend: true,
                    callback: function() {
                        window.close();
                    }
                }],
                header: WD.loadstringliteral("IDS_CAP0029"),
                image: "wdres/info.svg"
            });
            hideEditor();
            return;
        }
        $.get({
            url: approot + sid + "/edit/" + uriOrig,
            dataType: "text"
        }).then(function(data1) {
            dataOrig = data1;
            return $.get({
                url: approot + sid + "/edit/" + uriMod,
                dataType: "text"
            });
        }).done(function(data2) {
            dataMod = data2;
            var $container = $('#editfilecontainer');

            clearEditor();

            $container.empty();
            showEditor();
            var $tp = $("#theme-picker");
            var currentTheme = $tp.get(0).options[$tp.get(0).selectedIndex].value;

            // Set diff view (default to side-by-side, if no cookie)
            var $id = $('#inline-diff');
            var savedSideBySide = (getCookie("edsbs") === "false") ? false : true;
            $id.prop("checked", !savedSideBySide);

            editor = monaco.editor.createDiffEditor($container.get(0), {
                theme: currentTheme,
                renderSideBySide: savedSideBySide,
                readOnly: true // If host supported it, could edit while in diff mode
            });

            var originalModel = monaco.editor.createModel(dataOrig, language, monaco.Uri.file(uriOrig));
            var modifiedModel = monaco.editor.createModel(dataMod, language, monaco.Uri.file(uriMod));

            editor.setModel({
                original: originalModel,
                modified: modifiedModel
            });

            diffnav = monaco.editor.createDiffNavigator(editor, {
                followsCaret: true, // resets the navigator state when the user selects something in the editor
                ignoreCharChanges: true // jump from line to line
            });

            var $lp = $("#language-picker");
            $lp.get(0).value = originalModel.getModeId();

            $id.parent().removeClass("hidden");

            $('#diffnavprev').parent().removeClass("hidden");

            //$container.data("uri", sid + "/edit/" + uri);
            $container.data("uri", "diff:" + approot + sid + "/edit/" + uriOrig + ";" + approot + sid + "/edit/" + uriMod);

            editor.focus();
        }).fail(function(jqXHR, textStatus, errorThrown) {
            clearEditor();
            var msgErrorPrefix = WD.loadstringliteral("IDS_WEBERR0001", "Compare failed with the following error:"); 
            var msgError = msgErrorPrefix + "<br>" + errorThrown + " (" + jqXHR.status + ")";
            if (jqXHR.status == 404) {
                // use jQuery to html-encode url as it could be specified by a malicious actor
                msgError = msgError + " on file '" + $('<div/>').text(this.url).html() + "'";
            }
            WD.showmessage({
                msg: msgError,
                msgtype: "ERROR",
                button: [{
                    buttonlabel: WD.loadstringliteral("IDS_CAP0067"),
                    nosend: true,
                    callback: function() {
                        window.close();
                    }
                }],
                header: WD.loadstringliteral("IDS_ERROR0022"),
                image: "wdres/exclamation.svg"
            });
            hideEditor();
            return;
        });
    }

    /**
     * Saves any changes in the editor
     */
    function saveEditor() {
        // PUT content back to WD
        var $container = $('#editfilecontainer');
        xhr($container.data("uri"), "PUT", editor.getModel().getValue(monaco.editor.EndOfLinePreference.CRLF), function(jqXHR, err, data) {
            if (err) {
                console.error("err");
                WD.displaytoast({
                    msg: WD.loadstringliteral("IDS_WEBERR0002", "Failed to save file.") + "<br><br>" + jqXHR.responseText,
                    msgtype: "ERROR"
                });
                return;
            }

            hideEditor();
            clearEditor();
        });
    }
    /**
     * Opens an editor in a new tab
     * 
     * @param {Object} command - Command object
     * @param {string} command.type - DIFF-FILE
     * @param {string} command.uriOrig - URI to original copy of file (old)
     * @param {string} command.uriMod - URI to modified copy of file (new)
     * @param {string} command.language - Language override
     */
    function launcheditorwindow(command) {
        var targeturl;
        if (command.type == "DIFF-FILE") {
            targeturl = sid + "/diff?mod=" + encodeURIComponent(command.uriMod) + "&orig=" + encodeURIComponent(command.uriOrig);
        } else {
            targeturl = sid + "/view?orig=" + encodeURIComponent(command.uri);
        }

        window.open(targeturl);
    }
    // Utility Functions
    function htmlUnescape(str) {
        return str
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&');
    }
    // Set Cookie
    function setCookie(cname, cvalue, exdays) {
        var d = new Date();
        d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
        var expires = "expires=" + d.toUTCString();
        secure = "";
        if (location.protocol === "https:") {
            secure = "; secure";
        }
        document.cookie = cname + "=" + cvalue + ";" + expires + ";path=" + approot + secure;
    }
    // Get Cookie
    function getCookie(cname) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) == ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) == 0) {
                return c.substring(name.length, c.length);
            }
        }
        return "";
    }

    function getPromptObjects(id, partial, getnativeelems) {
        // getnativeelems will get you native htmlelemnts instead of jquery (only for non partial now)
        // get all objects that name ID
        var querystr = "[name='" + id + "']";
        if (partial) {
            // include rows (which always have prompt id + _ + row)
            querystr += ",[name*='" + id + "_']";
        }
        var promptobjs = getnativeelems ? document.querySelectorAll(querystr) : $(querystr);
        return promptobjs;
    }
    // Massage ID for use in jQuery selector (handles dots and things in ids)
    function jQueryID(promptID) {
        // Our Prompt ID's have : in them, which can confuse jQuery
        // http://api.jquery.com/category/selectors/#Special_characters_in_selectors
        return promptID.replace(/(!|"|#|\$|%|&|'|\(|\)|\*|\+|,|\.|\/|:|;|<|=|>|\?|@|\[|\\|\]|\^|`|{|\||}| |~)/g, '\\$1');
    }

    function addHandlers() {
        $(window).on("resize", function() {
            WD.repositionblocker();
            if (editor) {
                editor.layout();
            }
            WD.fixgridheader($(document));
        }).on("focus", function() {
            if ($("div.focuselement").length == 0) {
                // We must have tabbed right off the screen and the WD.tab is still pending when we come back, but it's meaningless now
                // We don't want alttab set under this condition, either, because focus is effectively lost and we want the jump to fire
                // Set to -1 to handle the fact window.focus fires multiple times before the element focus triggers
                if (WD.tab !== 0) {
                    WD.tab = -1;
                }
                else if (searching) {
                    // Searching with Ctrl+F falsely caused alttab to get set, losing some jump commands
                    searching = false;
                }
                else if (WD.tab == 0) {
                    alttab = true;
                }
            }
        });
        var isrequiredempty = false;
        $(document).on('click', '.nav-pills a', function(event) {
            // disable clicking on disabled boostrap nav pills
            // console.log("clicking on nav-pill",
            // $(this).parent('li').hasClass('disabled'));
            if ($(this).parent('li').hasClass('disabled')) {
                event.preventDefault();
                event.stopImmediatePropagation();
                return false;
            }
        }).on("dblclick", ".reactscreen", function(event) {
            var jElem = $(this);
            jElem.css({
                left: jElem.data("startcol") + "em",
                top: jElem.data("startrow") + "em"
            });
            WD.positionscreen(jElem);
            WD.positionmenubar(jElem, true);
        }).on("click", ".reactscreen", function(event) {
            var focusel = $(".focuselement");
            if (focusel.length > 0) {
                if (focusel.is(":focus") === false) {
                    if (dirtydata === null) {
                        focusel.trigger("focus");
                    }
                }
            }
        }).on("input keyup", ".prompt", function(event) {
            if (event.which !== 13 && event.which !== 9) {
                $(this).data("dirty", true);
            }
        }).on('keyup', '.grid table tbody tr', function(event) {
            // hotkeys script doesnt support the insert key for some reason
            if (event.which == 45) { // Insert Key
                WD.input(WD.ESCAPE + "F8", true);
            }
        }).on("blur", "input, textarea", function(event) {
            
            $('#promptliteral').html('')
            .attr("title", "");
            
            var target = event.target;
            var classList = target.classList;

            isrequiredempty = false;
            if (target.required && !target.value && classList.contains("prompt")) {
                previousfocusinput = target;
                event.preventDefault();
                isrequiredempty = true;
                return false;
            }
            
        }).on("keyup", "textarea.prompt", function(event) {
            WD.resizeTextarea(this);
        }).on("keydown", ".prompt", function(event) {
            
            var tagName =  (event.target.tagName || "").toLowerCase();
            var isTextArea = tagName === 'textarea'; 
            if (isTextArea) {
                WD.textareaKeyHandler(event);
            } 
            
            if ((tagName === 'input' || isTextArea) && event.key === 'Tab' && WD.tab !== 1 && $(event.target).parents(".screen").length !== 0) {
                WD.tab = 1; // In Some Cases hotkeys is not setting tab to 1 on screens, do it on keydown
            }

        }).on("change", ".promptcontainer input[type='text'].prompt,.promptcontainer input[type='password'].prompt,.promptcontainer textarea.prompt", function(event) {
            var evttarget = event.target;
            if (!evttarget.value && evttarget.required) {
                setTimeout(function() {
                    evttarget.focus();
                }, 80);
                WD.displaytoast({msg: WD.loadstringliteral("IDS_WEBERR01")});
                previousfocusinput = evttarget;
                return;
            }
            WD.updateelement(event,this);
        }).on("dragstart", ".promptcontainer input[type='text'].prompt,.promptcontainer input[type='password'].prompt,.promptcontainer textarea.prompt", function(event) {
            return false;
        }).on("click", ".promptcontainer input[type='radio'].prompt", function(event) {
            WD.updateelement(event,this);
            return false;
        }).on("focus", ".promptcontainer input[type='text'].prompt,.promptcontainer input[type='password'].prompt,.promptcontainer textarea.prompt", function(event) {
            var target = event.target;
            // In Jquery 3.7 focus event is triggered on disabled element too while in older it is not (added condition for compatibility)
            if (previousfocusinput && previousfocusinput.id != target.id && previousfocusinput.isConnected && isrequiredempty) {
                event.preventDefault();
                return false;
            }
            previousfocusinput = null;
            if (!target.disabled) {
                isrequiredempty = false;
                WD.focuselement(event, this.id);
                if (target.tagName.toLowerCase() !== 'textarea' && this.type == "password" && $(this).prop('readonly')) {
                    this.removeAttribute('readonly'); 
                }
            }

        }).on("click", ".menuitem", function(e) {
            // Highlight Menu Items
            var jthis = $(this);
            if (jthis.hasClass("selected")) {
                jthis.removeClass("selected");
            } else {
                $(".menuitem.selected").removeClass("selected");
                jthis.addClass("selected");
            }
        }).on("keydown", "body", function(event) {
            // detect crtl+c for elem
            if (event.target && event.target.tagName.toLowerCase() === 'body' && event.ctrlKey && event.code === 'KeyC' && navigator.clipboard) {
                var inputElem = $('.sshighlight input[disabled][type="text"].focuselement');
                if (inputElem.length > 0 && inputElem.val()) {
                    navigator.clipboard.writeText(inputElem.val());
                }
            }
        });
        // Stop Passthrough Clicks
        $('#windowblock').on("click", function(e) {
            e.stopPropagation();
            return false;
        });
        /*
         * Scroll vertically-fixed grid headers horizontally with body
         *
         * dom.on("scroll",".grid table tbody"... doesn't work with scroll event
         */
        document.addEventListener('scroll', WD.scrollhandler, true /*Capture event*/ );

        // Give message before leaving
        $(window).on('beforeunload', function() {
            if (selfreload || loggedout) {
                return;
            }

            var LEAVE_MESSAGE = WD.loadstringliteral("IDS_WEB0014", 'Leaving the page may cause loss of data. Are you sure you wish to leave?');
            if ($("#start").filter(isdisplayed).length == 0) {
                return LEAVE_MESSAGE;
            }
        });

        window.addEventListener('unload', function() {
            navigator.sendBeacon(approot + sid + "/logout");
        }, false);

        // setup question dialog window
        var questionwin = $("#question").children().first();
        questionwin.on("shown.bs.modal", function() {
            $("#questioninput").trigger("focus");
        }).on("keyup", function(e) {
            if (e.which == 13) {
                questionwin.find(".okbutton").trigger("click");
            } else if (e.which == 27) {
                questionwin.find(".cancelbutton").trigger("click");
            }
        });
    }


    // as a general note for all this hotkey stuff, any case where false is returned
    // prevents it from passing on the key press. I.E; F3 causes something to pop up in 
    // AFW, and the same keypress in Chrome opens up the Search bar.
    function setupHotkeys() {
        // by default hotkeys dont trigger from input-type prompts
        hotkeys.filter = function(e) {
            // allow all things to trigger hotkeys.
            // this can be modified to include certain types of prompts,
            // or even set scope based on types of prompts as well
            // i.e, make prompt-grid or prompt scopes and have hotkeys
            // registered off of those.
            return true;
        };

        //  Menu Scope hotkeys
        hotkeys('f1,left,up,right,down,enter', 'menu-selected', function(e, handler) {
            var selmenu = $(".menu", wcontainer).last().find(".menuitem.selected");
            if (selmenu.length > 0) {
                switch (handler.key) {
                    case "up":
                        selmenu.removeClass("selected");
                        var prevmenu;
                        if ($(".menu:last .menusection:first", wcontainer).is(selmenu.parent())) {
                            // if they are the first, go to the last menu section
                            prevmenu = $(".menu:last", wcontainer).find(".menusection:last");
                        } else {
                            prevmenu = selmenu.parent().prev(".menusection");
                        }
                        prevmenu.find(".menuitem:first", wcontainer).addClass("selected");
                        break;
                    case "down":
                        selmenu.removeClass("selected");
                        var nextmenu;
                        if ($(".menu:last .menusection:last", wcontainer).is(selmenu.parent())) {
                            // if they are the last, fo to the first menu section
                            nextmenu = $(".menu:last").find(".menusection:first");
                        } else {
                            nextmenu = selmenu.parent().next(".menusection");
                        }
                        nextmenu.find(".menuitem:first", wcontainer).addClass("selected");
                        break;
                    case "left":
                        selmenu.removeClass("selected");
                        if (selmenu.parent().find(".menuitem:first").is(selmenu)) {
                            // if they are first, go to the last in the row
                            selmenu.parent().find(".menuitem:last").addClass("selected");
                        } else {
                            selmenu.prev(".menuitem").addClass("selected");
                        }
                        break;
                    case "right":
                        selmenu.removeClass("selected");
                        if (selmenu.parent().find(".menuitem:last").is(selmenu)) {
                            // if they are last, go to the first in the row
                            selmenu.parent().find(".menuitem:first").addClass("selected");
                        } else {
                            selmenu.next(".menuitem").addClass("selected");
                        }
                        break;
                    case "enter":
                        selmenu.trigger("click");
                        break;
                    case "f1":
                        WD.input("?" + selmenu.attr("id"), false);
                        return false;
                }
            }
        });
        hotkeys("*", "menu", function() {
            // var keypressed = hotkeys.getPressedKeyCodes();
            // limit some keys maybe?
            //if (keypressed >= 91 && keypressed <= 46) { return false; }
            var selmenu = $(".menu", wcontainer).last().find(".menuitem.selected");
            if (selmenu.length == 0) {
                $(".menu", wcontainer).last().find(".menuitem:first").addClass("selected");
                // change scope so events dont double fire
                hotkeys.setScope("menu-selected");
            }
        });
        // show select hotkeys
        hotkeys('up,down,pageup,pagedown,enter', 'showselect', function(e, handler) {
            var row = $("tr").filter(".sshighlight").filter("[data-promptno='" + hostfocusprompt + "']");
            if (row.length > 0) {
                var currow = row.parent().children().index(row) + 1;
                var newrow = 0;
                if (handler.key == "enter") {
                    // treat as double click
                    var hascheckbox = (row.find(":checkbox").length > 0);
                    WD.ssdblclick(row, currow, true, !hascheckbox);
                } else {
                    switch (handler.key) {
                        case "up":
                            newrow = -1;
                            break;
                        case "pageup":
                            newrow = -5;
                            break;
                        case "down":
                            newrow = 1;
                            break;
                        case "pagedown":
                            newrow = 5;
                            break;
                    }
                    newrow = currow + newrow;
                    if (newrow > row.parent().children().length) {
                        newrow = 1;
                    }
                    if (newrow !== 0) {
                        // treat as single click
                        WD.ssprocessclick(row, newrow, false, (row.find(":checkbox").length == 0), true);
                        e.preventDefault();
                    }
                }
            }
        });
        //  Screen Scope hotkeys
        hotkeys("f1,f3,f8,tab,shift+tab,alt+down,enter,esc,up,down,pageup,pagedown", "screen", function(e, handler) {
            switch (handler.key) {
                case "f1":
                    WD.input(WD.ESCAPE + "F1", true);
                    return false;
                case "f8":
                    WD.input(WD.ESCAPE + "F8", true);
                    break;
                case "shift+tab":
                    WD.tab = 2;
                    break;
                case "tab":
                    WD.tab = 1;
                    break;
                case "enter":
                    // really, want to do an update element if the data has changed
                    var elem = $(e.target);
                    if (elem.parents(".screen").length > 0) {
                        if (elem.is(":button")) {
                            elem.trigger("click");
                            return false;
                        } else if (elem.data("dirty") != true) {
                            // nothing changed, so let's let the host move focus
                            // This goes against everything I stand for
                            blurprompt();
                            WD.senddata("R", true);
                            return false;
                        } else {
                            return true;
                        }
                    } else {
                        return true;
                    }
                    break;
                case "esc":
                    document.execCommand('undo', false, null);
                    break;
                case "alt+down":
                    WD.input(WD.ESCAPE + "?", true);
                    break;
                case "up":
                    if ($(".ui-autocomplete:visible").length === 0 && (e.target.id !== "tclinput")) {
                        blurprompt();
                        WD.senddata("U", true);
                    }
                    break;
                case "down":
                    if ($(".ui-autocomplete:visible").length === 0 && (e.target.id !== "tclinput")) {
                        blurprompt();
                        WD.senddata("D", true);
                    }
                    break;
                case "pagedown":
                    blurprompt();
                    WD.senddata("N", true);
                    break;
                case "pageup":
                    blurprompt();
                    WD.senddata("P", true);
                    break;
            }
        });
        //  Global Scope hotkeys
        hotkeys('f2,f3,f4,shift+f4,f5,f9,ctrl+f', function (e, handler) {
            switch (handler.key) {
                case "f2":
                    blurprompt();
                    WD.senddata("F2", true);
                    break;
                case "f3":
                    WD.input(WD.ESCAPE + "F3", true);
                    return false;
                case "shift+f4":
                    WD.input(WD.ESCAPE + "EXITTOLEVEL", true);
                    return false;
                case "f4":
                    WD.input(WD.ESCAPE + "F4", true);
                    return false;
                case "f5":
                    return false;
                case "f9":
                    WD.input(WD.ESCAPE + "F9", true);
                    break;
                case "ctrl+f":
                    searching = true;
                    break;
            }

        });
        //Editor scope hotkeys
        hotkeys('ctrl+s,ctrl+q,f3', "editor", function(e, handler) {
            switch (handler.key) {
                case "ctrl+s":
                    var ERR_MSG = WD.loadstringliteral("IDS_WEBERR0006", "Are you sure you wish to save and exit?");
                    WD.showmessage({
                        msg: ERR_MSG,
                        msgtype: "ERROR",
                        button: [{
                            buttonlabel: WD.loadstringliteral("IDS_CAP0095"),
                            nosend: true,
                            callback: function() {
                                $("#wdeditsave").trigger("click");
                            }
                        }, {
                            buttonlabel: WD.loadstringliteral("IDS_CAP0096"),
                            nosend: true
                        }],
                        header: WD.loadstringliteral("IDS_WEB0002", "Confirm save and exit") ,
                        image: "wdres/exclamation.svg"
                    });
                    return false;
                case "ctrl+q":
                    $("#wdeditcancel").trigger("click");
                    return false;
                case "f3":
                    return false;
            }
        });
    }

    function getpromptnum(promptid, includerow) {
        if (!promptid) {
            return 0;
        }
        var temp = promptid.split("_");
        if (includerow && temp.length > 2) {
            return temp[1] + "." + temp[2];
        } else {
            return temp[1];
        }
    }

    function blurprompt() {
        if (document.activeElement) {
            document.activeElement.blur();
        }
    }
    /*
     * Ensure that only one invocation is processed over some period of time
     */
    function processingevent(target, eventname, duration) {
        // target : DOM element, not string
        // eventname : eg. "click"
        // duration : Time to wait before resetting in milliseconds
        $target = $(target);
        eventname = eventname || "";
        duration = duration || 1000;
        dataname = "processing-" + eventname;

        if ($target.data(dataname)) {
            // Already processing
            return true;
        } else {
            // Start processing
            $target.data(dataname, true);
            setTimeout(function(target, data) {
                target.data(data, false);
            }, duration, $target, dataname);
            return false;
        }
    }

    function showupcancel() {
        var $tool = $("#COMMANDBAR_BAND_bndToolbarStandardCOMMANDBAR_TOOL_attCancelUp img, #COMMANDBAR_BAND_bndMenuStandardCOMMANDBAR_TOOL_attCancelUp img");
        if ($tool.length) {
            var src = $tool.attr("src");
            if ($(".screen", wcontainer).filter(isdisplayed).length) {
                // Have screen, show Cancel
                src = src.replace("uptool.svg", "canceltool.svg");
                
                $tool.attr("src",src);
                $tool.attr("title","Cancel");
                $tool.attr("alt","Cancel");
            } else {
                // Do not have screen, show Up
                src = src.replace("canceltool.svg", "uptool.svg");
                
                $tool.attr("src",src);
                $tool.attr("title","Up");
                $tool.attr("alt","Up");
            }
            
        }
    }
    // Public Stuff
    return {
        // Constants
        tab: 0,
        ESCAPE: String.fromCharCode(27),
        AM: String.fromCharCode(254),
        VM: String.fromCharCode(253),
        SM: String.fromCharCode(252),
        // Functions
        init: function() {
            mainwindow = true;
            window.name = "WD_" + sid.substr(0, 8);
            setupTerminal();
            setupLogin();
            setupHotkeys();
            addHandlers();
            setupEditor();
            checkBrowser();
            addWindowListener();
            var storedmsg = sessionStorage.getItem("message");
            if (storedmsg) {
                WD.displaytoast({
                    "msg": storedmsg,
                    "msgtype": sessionStorage.getItem("msgtype")
                });
                sessionStorage.removeItem("message");
                sessionStorage.removeItem("msgtype");
            }
        },
        gettcl: function() {
            return $("#tcl").children().first();
        },
        showtcl: function() {
            WD.gettcl().addClass('show');
            WD.hideconnecting();
            setTerminalSize();
            WD.tclsetfocus();
            WD.ready();
            terminal.scrollToBottom();
        },
        hidetcl: function() {
            WD.gettcl().removeClass("show");
            var focusel = $(".focuselement");
            if (focusel.length > 0 && focusel.filter(":focus").length == 0) {
                focusel.trigger("focus");
            }
        },
        toggletcl: function() {
            if (WD.gettcl().hasClass("show")) {
                WD.hidetcl();
            } else {
                WD.showtcl();
            }
        },
        tclsetfocus: function() {
            if (!$("#output .xterm-helper-textarea").is(':focus') && !$("#tclinput").is(':focus')) {
                $("#tclinput").trigger("focus");
            }
            WD.cleartclwait();
        },
        requestlogout: function() {
            var request = WD.ESCAPE + "WDD" + WD.AM + "EXIT";
            WD.input(request);
        },
        logout: function(command) {
            selfreload = true;
            WD.delayedtoast(command);
            var newloc;
            if (autoconnect) {
                newloc = approot + "loggedout/" + loginserver;
                newloc = newloc.replace("//", "/");
                window.location = newloc;
                //$("body").load("/loggedout");
            } else if (serveroverride) {
                newloc = approot + serveroverride;
                if (accountoverride) {
                    newloc += "/" + accountoverride;
                }
                newloc = newloc.replace("//", "/");
                window.location = newloc;
            } else {
                // A logout should be a clean thing
                // Let error messages display, if navigating to external error page
                setTimeout(function() {
                    window.location.reload();
                }, 1); // DoEvents, then reload
            }
        },
        oldlogout: function() {
            // deprecated code
            // reset ourselves to the base
            loggedout = true;
            WD.closeallbrowsers();
            WD.initui();
            terminal.clear();
            keepTCLhidden = true;
            WD.hideconnecting();
            WD.hidetcl();
            WD.cleartclwait();
            $(".wdbg").show();
            WD.showstart();
            $("#devout").hide();
            $("#logoutbutton").hide();
            WD.enablescreens();
            document.title = $("body").data("origtitle");
            $("#statusbar").hide();
        },
        initui: function() {
            wcontainer.empty().hide();
            if (isgc) {
                wcontainer.css('left', $("#commandbarcontainer").outerWidth());
            } else {
                wcontainer.css('left', 0);
            }
            $("#commandbarcontainer").empty().hide();
            WD.updateprogressbar({
                close: true
            });
            $("#WGBGB_1").hide();
        },
        showstart: function() {
            $("#start").show()
                .find("input").prop("disabled", false);
        },
        hidestart: function() {
            $("#start").hide()
                .find("input").prop("disabled", true);
        },
        cleartclwait: function() {
            if (idletimerid !== 0) {
                clearTimeout(idletimerid);
                idletimerid = 0;
            }
            $("#tcltoggle").removeClass("tclactivity tclwaiting");
        },
        enablescreens: function() {
            //$("#thescreens").attr("disabled",false);
            //$("input").prop("readonly", false);
            //screensdisabled = false;
        },
        disablescreens: function() {
            //$("#thescreens").attr("disabled",true);
            //$("input").prop("readonly", true);
            //screensdisabled = true; 
        },
        writeTCL: function(tcldata) {
            // buffer the screen so we have it for scrollback
            var clearcode = WD.ESCAPE + "[2J";
            if (isgc) {
                clearcode = WD.ESCAPE + "[J";
            }
            if (tcldata.indexOf(clearcode) >= 0) {
                tcldata = tcldata.replaceAll(clearcode, String.fromCharCode(10).repeat(tclrows) + clearcode);
            }
            terminal.write(htmlUnescape(tcldata));
            var tcltoggle = $("#tcltoggle"); 
            tcltoggle.addClass("tclactivity");
            if ($(".screen,.menu", wcontainer).length == 0 && !keepTCLhidden) {
                // auto show if we don't have a menu / screen
                WD.showtcl();
            } else if (itemqueue.length == 0 && !keepTCLhidden) {
                // show right away if nothing after this
                WD.showtcl();
            } else if (idletimerid === 0) {
                idletimerid = setTimeout(function() {
                    if (idletimerid !== 0) {
                        tcltoggle.addClass("tclwaiting").removeClass("tclactivity");
                        idletimerid = 0;
                        if (!loggedout) {
                            // don't show if we've already been logged out
                            WD.showtcl();
                        }
                    }
                }, MAX_TCL_IDLE_TIME);
            }
        },
        processqueueitem: function() {
            sentdata = true;
            itemqueueprocessed = false;
            // console.log("processqueueitem");

            var cmdpromptmap = {};
            var tclcleared = false;
            var isscreeninqueue = false;
            var flash_msg_target;

            while (itemqueue.length > 0) {
                resp = itemqueue.shift();
                // console.log(resp.datatype, itemqueue);
                if (resp.datatype === "TCL") {
                    if (resp.tcldata !== "") {
                        WD.writeTCL(resp.tcldata);
                    }
                } else if (resp.datatype === "COMMAND") {
                    // Command from WebDirect

                    var respcommand = resp.command;
                    var is_display_cmd = respcommand.type === "DISPLAY";
                    var is_flash_msg = respcommand.msgtype === "FLASH";

                    if (!tclcleared || !is_display_cmd) {
                        WD.cleartclwait();
                        WD.hidetcl();
                        tclcleared = true;
                    }

                    if (is_flash_msg) {
                        flash_msg_target = flash_msg_target === undefined ? respcommand.targetid : null;
                    }

                    var resptarget = is_display_cmd? String(respcommand.targetid || "").split("_", 1)[0] : undefined;
                    var cmdprompts = is_display_cmd? cmdpromptmap[resptarget] : undefined;

                    if (is_display_cmd && resptarget && !cmdprompts) {
                        var cmdpromptstemp = document.querySelectorAll('[name^="' + resptarget + '"]');
                        cmdprompts = {};

                        cmdpromptstemp.forEach(function(elem) {
                            var elemname = elem.getAttribute("name");
                            var cmpprompt = cmdprompts[elemname];
                            if (!cmpprompt) {
                                cmpprompt = cmdprompts[elemname] = [];
                            }
                            cmpprompt.push(elem);
                        });
                        cmdpromptmap[resptarget] = cmdprompts;
                    }

                    if (is_display_cmd && respcommand.focus && !isscreeninqueue && flash_msg_target && !respcommand.mvndx) {
                        respcommand.flash_msg_target = flash_msg_target;
                    }

                    if (is_display_cmd && cmdprompts) {
                        WD.displayprompt(respcommand, cmdprompts);
                    } else {
                        WD.runcommand(respcommand);
                    }

                    if (resp.prompting) {
                        WD.ready();
                        WD.doneconnecting();
                    }
                } else if (resp.datatype === "") {
                    // nothing to do
                } else {
                    // Render Object From Host
                    WD.cleartclwait();
                    WD.hidetcl();

                    var isScreen = resp.datatype === "SCREEN";
                    isscreeninqueue = isscreeninqueue || isScreen;
                
                    var renderedarray = WD.render(resp);
                    var rendered = renderedarray[0];
                    var renderedstr = renderedarray[1] || "";
                    if (!rendered) {
                        // still waiting for data from the host, put us back on and pop
                        itemqueue.unshift(resp);
                        return;
                    } 
                }
            }
            // done processing items, make sure right item has focus
            WD.enablescreens();
            var focusel = $(".focuselement");
            if (focusel.length > 0 && focusel.filter(":focus").length == 0 && !WD.gettcl().is(":visible")) {
                focusel.trigger("focus");
            }
            sdrag = $(".screen", wcontainer).last().children();
            if (sdrag.length > 0 && sdrag.data("position") !== "FULLSCREEN") {
                sdragparent = sdrag.parent();
                sdragparentpos = sdragparent.position();
                sdrag.draggable({
                    containment: [sdragparentpos.left - 400,
                        sdragparentpos.top - 400,
                        sdragparentpos.left + sdragparent.outerWidth() + 400,
                        sdragparentpos.bottom + sdragparent.outerHeight() + 400
                    ],
                    start: function(event, ui) {
                        WD.positionmenubar($(this), true);
                    },
                    drag: function(event, ui) {
                        WD.positionmenubar($(this), true);
                    },
                    stop: function(event, ui) {
                        WD.positionmenubar($(this), true);
                        var focusel = $(".focuselement");
                        if (focusel.length > 0) {
                            focusel.trigger("focus");
                        }
                    }
                });
            }
            WD.ready();
            WD.startpoll();
            sentdata = false;
            itemqueueprocessed = true;
            
            while (clickqueue.length > 0) {
                clickqueue.shift().trigger("click");
            }
            // console.log("processqueue ends")
        },
        processresponse: function(response) {
            if (!mainwindow) {
                return;
            }
            // handle responses
            if (response && response.login) {
                selfreload = true;
                window.location.reload();
            } else if (response && response.results.length > 0) {
                // console.log(response.results);
                itemqueue.push.apply(itemqueue, response.results);
                if (response.renderids.length > 0) {
                    // wait for render data
                    // console.log("Renders for ", response.renderids);
                    $.post(sid + "/render", {
                        id: JSON.stringify(response.renderids)
                    }, function(data) {
                        // console.log(response.renderids, data);
                        previousfocusinput = null;
                        Object.assign(renderdataqueue, data);
                        WD.processqueueitem();
                    }).fail(function() {
                        WD.logout({
                            msg: WD.loadstringliteral("IDS_WEBERR0003", "Connection has been lost"),
                            msgtype: 'ERROR'
                        });
                    }).always(WD.ready.bind(this));
                } else {
                    WD.processqueueitem();
                }
            } else {
                WD.startpoll();
            }
        },
        render: function(response) {
            // render item in UI
            // Will need a way to add buttons to toolbar
            var itemid = response.targetid;
            var datatype = response.datatype;
            var itemtoload = null;
            var wc = wcontainer;
            var renderid = "r" + response.renderid;
            // early check to see if we have the data yet
            var renderdata = renderdataqueue[renderid];
            if (renderdata == undefined || renderdata == null) {
                return [false, ""];
            }
            // remove from object
            delete renderdataqueue[renderid];
            // console.log(itemid, renderdata);
            var screentoload = false;
            if (response.datatype === "COMMANDBAR") {
                wc = $("#commandbarcontainer");
                wc.html("<div id='" + itemid + "'></div>");
            } else if (response.datatype === "COMMANDBARTOOL") {
                itemid = response.parentid + itemid;
                var insertpos = response.position;
                var itempos = -1;
                wc = $("#commandbarcontainer");

                // Remove seperator if exists (it will be added again as part of button html)
                var $itemsep = $("#" + jQueryID(itemid + "-sep"), wc);
                if ($itemsep.length) {
                    $itemsep.remove();
                }

                // Get item or create placeholder if doesn't already exist
                var $item = $("#" + jQueryID(itemid), wc);
                if ($item.length) {
                    itempos = $("#" + jQueryID(response.parentid) + " > li", wc).index($item);
                    if (insertpos > itempos) {
                        // Adjust insertion index if item is moving down/right
                        insertpos += 1;
                    }
                } else {
                    $item = $("<div/>", {
                        id: itemid
                    });
                }

                // Find insertion point for new/updated tool
                var $parentband = $("#" + jQueryID(response.parentid), wc);
                if ($parentband.length) {
                    /*
                     * nth-child is 1-based, insertpos is 0-based so this effectively
                     * selects the n-1th element (the one before)
                     */
                    if (insertpos >= 0) {
                        var $insertionpoint = $("#" + jQueryID(response.parentid) + " > :nth-child(" + insertpos + ")", wc);
                        if ($insertionpoint.length) {
                            // If I can find element at position-1, add after element
                            if (insertpos != itempos) {
                                // Only insert/move if item is in different location
                                $insertionpoint.after($item);
                            }
                        } else {
                            // if I have an empty band or can't find item, add inside band
                            $parentband.prepend($item);
                        }
                    }
                }
            } else if (response.datatype === "BGBROWSER") {
                if (itemid == "WGBGB_1") {
                    if ($("body").find("#" + itemid).length === 0) {
                        wc.before("<div id='" + itemid + "' class='" + response.datatype.toLowerCase() + "'></div>");
                    }
                } else {
                    if (wc.find("#" + itemid).length === 0) {
                        wc.append("<div id='" + itemid + "' class='" + response.datatype.toLowerCase() + "'></div>");
                    }
                }
            } else if (["SCREEN", "MENU"].indexOf(datatype)!==-1) {

                var datatypelower = datatype.toLowerCase();
                hotkeys.setScope(datatypelower);
                itemid = itemid + "_" + datatypelower;
                screentoload = $("#" + jQueryID(itemid)).length === 0;
                if (screentoload) {
                    wc.append("<div id='" + itemid + "' class='" + datatypelower + "'></div>");
                }
            } else if (datatype === "MENUBAR") {
                itemtoload = wc.find(".wdmenubar");
                if (itemtoload.length === 0) {
                    wc.append("<div id='" + itemid + "' class='wdmenubar'></div>");
                    itemtoload = wc.find(".wdmenubar");
                }
            } else if (["PROMPT", "GRID", "BUTTON", "TEXT"].indexOf(datatype)!==-1) {
                var screenObj = $("#" + response.targetid.split("_")[0] + "_screen").find(".subscreen");
                if (screenObj.find("#" + jQueryID(itemid)).length === 0) {
                    if (response.datatype === "PROMPT") {
                        var scrollable = screenObj.find(".scrollable");
                        if (scrollable.length > 0) {
                            screenObj = scrollable
                        }
                        screenObj.append("<span id='" + itemid + "' class='promptcontainer'></span>");
                    } else {
                        screenObj.append("<span id='" + itemid + "'></span>");
                    }
                }
            }
            // Make sure container shows
            wc.show();
            if ($("#start").filter(isdisplayed).length > 0) {
                WD.hidestart();
            }

            var activeId = document.activeElement.id;
            var targetid = activeId ? response.targetid : "";
            var tagname = document.activeElement.tagName.toLowerCase();
            // if focus is on previous screen shift to current subscreen
            if (screentoload && targetid && activeId.indexOf(targetid) === -1 && ['input', 'button'].indexOf(tagname) !== -1) {
                /* 
                    If in previous screen focus was on input or button (blur doesn't take away tab functionality), 
                    creating new button adding to the screen and reset focus
                    # SEE: https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/focus
                */
                var tempBt = $("<button></button>");
                var item = $("#" + itemid);
                item.append(tempBt[0]);
                tempBt[0].focus();
                tempBt.remove();
            }
            // console.log("render",response, itemid);
            itemtoload = itemtoload || $("#" + jQueryID(itemid));
            if (itemtoload.length > 0) {
                if (response.datatype === "PROMPT") {
                    var origitem = itemtoload;
                    itemtoload = itemtoload.closest(".promptcontainer");
                    if (itemtoload.length === 0) {
                        // failed to find closest container
                        itemtoload = origitem;
                    }
                    // I'd rather only remove these when I'm sure the load works
                    // Would need to mark them somehow. Set a data tag?
                //    $("label[for='" + itemid + "']", wcontainer).remove();
                }
                // console.log("Render for ", response.renderid, renderdata.html(), data, itemtoload);
                var data;
                if (response.datatype === "GRID") {
                    var proptext = renderdata;
                    try {
                        var propdict = JSON.parse(proptext);
                        screens[0].addGrid(propdict);
                        data = $(itemtoload[0]);
                    } catch (e) {
                        console.log("Error parsing renderdata", renderdata, e);
                    }
                } else if (response.datatype === "PROMPT") {
                    var proptext = renderdata;
                    try {
                        var propdict = JSON.parse(proptext);
                        screens[0].addPrompt(propdict);
                    } catch (e) {
                        console.log("Error parsing renderdata", renderdata, e);
                    }
                } else if (response.datatype === "BUTTON") {
                    var proptext = renderdata;
                    try {
                        var propdict = JSON.parse(proptext);
                        screens[0].addButton(propdict);
                    } catch (e) {
                        console.log("Error parsing renderdata", renderdata, e);
                    }
                } else if(response.datatype === "TEXT"){
                    var proptext = renderdata;
                    try {
                        var propdict = JSON.parse(proptext);
                        screens[0].addText(propdict);
                    } catch (e) {
                        console.log("Error parsing renderdata", renderdata, e);
                    }
                } else if (response.datatype === "SCREEN") {
                    if (screens.length > 0 && response.targetid === screens[0].props.screenid) {
                        WDC.unmountComponentAtNode(itemtoload[0]);
                        screens.shift();
                    }
                    var proptext = renderdata;
                    try {
                        var propdict = JSON.parse(proptext);
                        propdict["scheme"] = structuredClone(schemesettings);
                        propdict["isgc"] = $("body").hasClass("gc")
                        screens.unshift(WDC.render(WDC.createElement(WDC.Screen, propdict), itemtoload[0]));
                        data = $(itemtoload[0]);
                    } catch (e) {
                        console.log("Error parsing renderdata", renderdata, e);
                    }
                } else {
                    data = $(renderdata)
                    itemtoload.replaceWith(data);
                }
                if (data) {
                    WD.processrender(data);
                    WD.applyscheme(data);
                }
            }
            return [true, renderdata];
        },
        processrender: function(renderitem) {
            childScreen = renderitem.children('.reactscreen');
            if (renderitem.is(".screen, .menu")) {
                if (wcontainer.children(".screen,.bgbrowser,.menu").last().is(".bgbrowser")) {
                    // need to move our screen/menu to after the browser
                    renderitem.after(wcontainer.children(".screen,.bgbrowser,.menu").last());
                }
                if (renderitem.is(".screen")) {
                    WD.positionscreen(childScreen);
                    if (renderitem.is(isdisplayed)) {
                        WD.positionmenubar(renderitem);
                    }
                    var focusprompt = childScreen.data("focuspromptid");
                    if (focusprompt !== undefined && focusprompt !== null && focusprompt != "") {
                        WD.hostfocus(focusprompt);
                    } else {
                        // at least remove focus from previous item
                        if (document.activeElement) {
                            document.activeElement.blur();
                        }
                    }
                    childScreen.removeAttr("data-focuspromptid");
                    renderitem.prevAll().find("input,textarea:not([readonly]),button").prop("readOnly", true).addClass("tempreadonly");
                    WD.addautocomplete(renderitem);
                    WD.fixgridheader(renderitem);
                }
                WD.repositionblocker();
            } else if (renderitem.is(".navbar")) {
                jQuery.SmartMenus.Bootstrap.init();
            } else if (renderitem.parents(".navbar").length) {
                $(".nav").smartmenus('refresh');
            } else if (renderitem.is(".bgbrowser")) {
                if (renderitem.get(0).id == "WGBGB_1") {
                    if (renderitem.is(isdisplayed)) {
                        wcontainer.css('left', renderitem.css("width"));
                    } else {
                        if (isgc) {
                            wcontainer.css('left', $("#commandbarcontainer").outerWidth());
                        } else {
                            wcontainer.css('left', 0);
                        }
                    }
                } else {
                    if (renderitem.is(isdisplayed) && renderitem.data("zorder") == "0") {
                        wcontainer.append(renderitem);
                    }
                    WD.repositionblocker();
                }
            } else if (renderitem.is(".wdmenubar")) {
                WD.positionmenubar($(".screen", wcontainer).last());
            }

            if (renderitem.is(".grid")) {
                var renderitemparent = renderitem.parent(); 
                WD.addautocomplete(renderitemparent);
                WD.fixgridheader(renderitemparent);
            }
            WD.hidetcl();
            // console.log("done rendering");
            showupcancel();
        },
        addautocomplete: function(parent) {
            var inputs = parent.find("input").filter("[data-list]");
            inputs.each(function() {
                var prompt = $(this);
                prompt.on("focus", function() {
                    prompt.autocomplete({
                        source: WD.getaclist(prompt)
                    });
                });
            });
        },
        getaclist: function(prompt) {
            var listid = jQueryID(prompt.data("list"));
            var list = $("#" + listid);
            var results = [];
            list.find("option").each(function() {
                results.push(this.value);
            });
            return results;
        },
        fixgridheader: function(gridparent) {
            var theads = gridparent.find(".grid thead");
            theads.each(function() {
                var $thead = $(this);
                var trs = $thead.find("tr");
                $thead.css({ minHeight: trs.outerHeight() + 2 });

                var $tbody = $thead.closest('table').find('tbody');
                var $headrow = $thead.find('tr:first');
                var $bodyrow = $tbody.find('tr:first');
                var scrollallowance = 50;
                if ($bodyrow && $headrow && $headrow.width() !== $bodyrow.width()) {
                    // Sync up row widths

                    // Add padding to last col for scrollbar discrepancy
                    if ($headrow.find("th").length > 1) {
                        $headrow.width($bodyrow.width());
                        $lastheadcol = $headrow.find("th:last");
                        var slicesize = $lastheadcol.attr("colspan") * -1;
                        var cols = $bodyrow.find("td").slice(slicesize);
                        var colwidth = 0;
                        cols.each(function() {
                            colwidth += $(this).width();
                        });
                        $lastheadcol.css({
                            minWidth: (colwidth + scrollallowance) + "px"
                        });
                    } else {
                        $headrow.width($bodyrow.width() + scrollallowance);
                    }
                }
            });
        },
        scrollhandler: function(e) {
            var target = e.target;
            if (target) {
                var $tbody = $(target);
                if ($tbody.is("div")) {
                    var $thead = $tbody.closest('table').find('thead');
                    $thead.scrollLeft($tbody.scrollLeft());
                }
            }
        },
        positionscreen: function(renderitem) {
            var screenpos = renderitem.data("position");
            if (screenpos && screenpos !== "" && screenpos !== "FULLSCREEN") {
                var target = wcontainer;
                // center is default
                var my = "center center";
                // move screen to correct location
                if (screenpos === "BOTTOMRIGHT") {
                    my = "right bottom";
                } else if (screenpos === "TOPRIGHT") {
                    my = "right top";
                } else if (screenpos === "BOTTOMLEFT") {
                    my = "left bottom";
                } else if (screenpos === "TOPLEFT") {
                    my = "left top";
                } else if (screenpos === "TOPCENTER") {
                    my = "center top";
                } else if (screenpos === "BOTTOMCENTER") {
                    my = "center bottom";
                }
                if (screenpos === "CENTER") {
                    var prevscreen = wcontainer.find(".reactscreen").not(renderitem).last();
                    if (prevscreen.length > 0 && prevscreen.is(isdisplayed) && prevscreen.position().left >= 0 && prevscreen.data("position") !== "FULLSCREEN") {
                        var calldifference = parseInt(prevscreen.data('screenid')) - parseInt(renderitem.data('screenid'));
                        // need to make sure it's also not smaller than the new window
                        if (calldifference < 2 && prevscreen.data("endrow") == renderitem.data("endrow") && prevscreen.height() >= renderitem.height()) {
                            my = "center bottom";
                            target = prevscreen;
                        }
                    }
                }
                renderitem.position({
                    my: my,
                    at: my,
                    of: target
                });
            }
            if (renderitem.data("startrow") >= 0) {
                // make sure screen fits if we have room for it
                var bottom = renderitem.position().top + renderitem.outerHeight();
                var top = renderitem.position().top;
                var right = renderitem.position().left + renderitem.outerWidth();
                // console.log(bottom, right, wcontainer.prop("clientHeight"), wcontainer.prop("clientWidth") );
                // need to find scrollable tbody
                if (top < 0) {
                    // if we are off the top of the screen, move us down
                    renderitem.css({
                        top: 0
                    });
                } else if (bottom > wcontainer.prop("clientHeight") && renderitem.outerHeight() < wcontainer.prop("clientHeight") && renderitem.position().top > 0) {
                    renderitem.css({
                        top: (renderitem.position().top - (bottom - wcontainer.prop("clientHeight")))
                    });
                    // console.log("moved screen up by", (bottom - wcontainer.prop("clientHeight")));
                }
                if (right > wcontainer.prop("clientWidth") && renderitem.outerWidth() < wcontainer.prop("clientWidth") && renderitem.position().left > 0) {
                    renderitem.css({
                        left: (renderitem.position().left - (right - wcontainer.prop("clientWidth")))
                    });
                    // console.log("moved screen left by", (right - wcontainer.prop("clientWidth")));
                }
            }
        },
        runcommand: function(command) {
            // console.log("Command", command);
            // run command
            switch (command.type) {
                case "INITUI":
                    WD.initui();
                    break;
                case "DONELOG":
                    loggedout = true;
                    break;
                case "UPDATETITLE":
                    document.title = command.value;
                    break;
                case "UPDATETEXT":
                    WD.updatetext(command);
                    break;
                case "MAIL":
                    WD.updatemailstatus(command);
                    break;
                case "LOGOUT":
                    WD.logout(command);
                    break;
                case "NAVEXT":
                    itemqueue.length = 0;
                    window.location.href = command.exturl + "&return=" + encodeURI(window.location.href);
                    break;
                case "MSG":
                    // message
                    // this should just be for flash messages
                    // everything else should be an alert
                    if (command.msgtype == "FLASH") {
                        if (command.msg != "") {
                            WD.displaytoast(command);
                        }
                    } else {
                        WD.showmessage(command);
                    }
                    break;
                case "DISPLAY":
                    WD.displayprompt(command);
                    break;
                case "UPDATEPROMPT":
                    WD.updateprompt(command);
                    break;
                case "STATUSBAR":
                    WD.updateprogressbar(command);
                    break;
                case "MENUBAR":
                    WD.updatemenubar(command);
                    break;
                case "CLOSEMENU":
                case "CLOSESCREEN":
                    WD.closecommand(command);
                    showupcancel();
                    break;
                case "CLEARFLASH":
                    WD.cleartoast();
                    break;
                case "FIREEVENT":
                    WD.fireevent(command, true);
                    break;
                case "UPDATEBROWSER":
                    WD.updatebrowser(command);
                    break;
                case "EXTERNALBROWSER":
                    WD.externalbrowser(command);
                    break;
                case "INSERTMV":
                    screens[0].insertRowInGrid(command.prompt, command.mvpos);
                    break;
                case "DELETEMV":
                    screens[0].deleteRowFromGrid(command.prompt, command.mvpos);
                    break;
                case "WAITONBUTTON":
                    hostfocusprompt = 0;
                    dirtydata = null;
                    dirtydataprompt = 0;
                    $("#" + jQueryID(command.targetid)).trigger("focus").addClass("focuselement");
                    break;
                case "DONECONNECTING":
                    WD.doneconnecting();
                    break;
                case "SHOWTCL":
                    WD.showtcl();
                    break;
                case "DELITEM":
                    // console.log(command.targetid);
                    $("#" + jQueryID(command.targetid)).remove();
                    break;
                case "CHANGECOLOUR":
                    // maintain list based on areas and just update info each time
                    var schemeobj = {
                        "element": command.targetid,
                        "area": command.area
                    };
                    if (command.colour !== "") {
                        schemeobj.colour = command.colour;
                    }

                    schemesettings[command.area] = schemeobj;
                    WD.applyscheme();
                    if (screens.length > 0) {
                        screens[0].updateScheme(schemeobj);
                    }
                    break;
                case "FILEPICKER":
                    WD.ready();
                    WD.selectfile(command);
                    break;
                case "EDITFILE":
                    if (command.readonly) {
                        launcheditorwindow(command);
                    } else {
                        loadEditorContent(command.uri, command.language, command.readonly);
                    }
                    break;
                case "DIFF-FILE":
                    launcheditorwindow(command);
                    break;
                case "UPDATEACLIST":
                    WD.updateaclist(command);
                    break;
                case "QUESTION":
                    WD.askquestion(command);
                    break;
                case "INFO":
                    WD.getinfo(command);
                    break;
                case true:
                    alert(WD.loadstringliteral("IDS_WEBERR0004", "unknown command type:") + " " + command.type);
                    break;
            }
        },
        connect: function(event, root, captcha_val) {
            if (!mainwindow) {
                return;
            }
            // Makes Connection to Host Universe
            window.history.replaceState("", "Connect", approot);
            connecturl = sid + "/connect";
            rootelem = $("#" + root);

            var enable_logging = rootelem.find("#loggingsessioncheck").prop("checked");
            reqdata = {
                user: rootelem.find("#username").val(),
                password: rootelem.find("#password").val(),
                server: rootelem.find("#server").val(),
                account: rootelem.find("#account").val(),
                passcode: rootelem.find("#passcode").val(),
                captcha: captcha_val,
                logging: enable_logging
            };
            if (rootelem.find("#ssl:checked").length > 0) {
                reqdata.ssl = "Y";
            }
            WD.cleartoast();
            $.ajax({
                url: connecturl,
                method: "POST",
                data: reqdata
            }).done(function(data) {
                connected = data.connect ? data.connect : 0;
                relogin = data.login ? data.login : 0;
                failed = data.error ? data.error : 0;
                if (connected) {
                    // $("#start").hide();
                    // $("#tclinput").trigger("focus");
                    sid = data.sid;
                    loggedout = false;
                    WD.showconnecting();
                    WD.startpoll();
                    // Clear credentials for next session
                    rootelem.find("#username").val("");
                    rootelem.find("#password").val("");
                } else if (relogin) {
                    WD.logout({
                        msg: data.error,
                        msgtype: 'ERROR'
                    });
                } else if (failed) {
                    WD.displaytoast({
                        msg: data.error,
                        msgtype: "ERROR"
                    });
                } else {
                    WD.logout();
                }
            });
            event.preventDefault();
        },
        autoconnect: function() {
            if (!mainwindow) {
                return;
            }
            // Makes Connection to Host Universe
            connecturl = sid + "/connect";
            connecting = true;
            $.ajax({
                url: connecturl,
                method: "POST"
            }).done(function(data) {
                connected = data.connect ? data.connect : 0;
                relogin = data.login ? data.login : 0;
                failed = data.error ? data.error : 0;
                if (connected) {
                    sid = data.sid;
                    loggedout = false;
                    WD.startpoll();
                } else if (relogin) {
                    WD.logout({
                        msg: data.error,
                        msgtype: 'ERROR'
                    });
                } else if (failed) {
                    WD.displaytoast({
                        msg: data.error,
                        msgtype: "ERROR"
                    });
                } else {
                    WD.logout();
                }
            });
            autoconnect = true;
        },
        runlogfile: function() {
            if (!mainwindow) {
                return;
            }
            $("#devout").show();
            // Runs a log file on the server
            connecturl = sid + "/logfile";
            reqdata = {
                logfile: $("#logfilename").val(),
                logdelay: $("#logdelay").val()
            };
            $.ajax({
                url: connecturl,
                method: "GET",
                data: reqdata
            }).done(function(data) {
                if (data && data.error) {
                    WD.displaytoast({
                        msg: data.error,
                        msgtype: "ERROR"
                    });
                } else {
                    loggedout = false;
                    WD.hidestart();
                    WD.startpoll();
                }
            });
        },
        firetlb: function(e, prompt) {
            // Fire Table Lookup for Prompt
            var jPrompt = $(prompt);
            if (jPrompt.is(":disabled")) {
                return false;
            }
            if (getpromptnum(jPrompt.siblings("input").first().get(0).id, true) != hostfocusprompt) {
                WD.updateelement(e, jPrompt.siblings("input").first().get(0), WD.ESCAPE + "?");
                return false;
            }
            if (dirtydata !== WD.ESCAPE + "?") {
                if (dirtydata !== null && dirtydata != "") {
                    WD.input("?" + dirtydata);
                } else {
                    WD.input(WD.ESCAPE + "?");
                }
                dirtydata = null;
                jPrompt.addClass("active");
            }
        },
        updateelement: function(e, prompt, optvalue) {
            // update an element
            // may need to do something with promptid in future
            // only trust things which are user initiated - isTrustred in
            // Chrome/Firefox or
            // which if initiated from mouse/keyboard (all browsers)
            // ie: don't want focus() calls to send something to the host
            // console.log("UpdateElement",prompt.id, optvalue, prompt.value);
            $("#promptliteral").html("")
                .attr("title", "");

            var jPrompt = $(prompt);
            var value = prompt.value;
            var promptid = prompt.id;
            var origvalue = jPrompt.data("orig");
            if (optvalue != null && optvalue != undefined) {
                value = optvalue;
            } else if (prompt.type == undefined || prompt.type == null) {
                // do nothing
            } else if (prompt.type == "checkbox") {
                if (jPrompt.is(":checked")) {
                    value = jPrompt.data('checkedvalue');
                } else {
                    value = jPrompt.data('uncheckedvalue');
                }
                if (jPrompt.parents(".multiselect").length == 0) {
                    value = value + WD.AM + WD.ESCAPE + "J" + getpromptnum(promptid) + ".0";
                }
                if (getpromptnum(promptid, false) == hostfocusprompt) {
                    // we're good as is
                } else {
                    // let host know we've tried to move here
                    WD.senddata(WD.ESCAPE + "J" + getpromptnum(promptid) + ".0");
                    sentdata = true;
                }
                //if (!jPrompt.hasClass("focuselement")) {
                //    value = WD.ESCAPE + "J" + getpromptnum(promptid) + ".0" + WD.AM + value;
                //}
            } else if (prompt.type == "radio") {
                jPrompts = getPromptObjects(prompt.name);
                // console.log("current focus",getpromptnum(prompt.name,false),hostfocusprompt);
                promptid = prompt.name;
                value = value + WD.AM + WD.ESCAPE + "J" + getpromptnum(promptid) + ".0";
                if (getpromptnum(promptid, false) == hostfocusprompt) {
                    // we're good as is
                } else {
                    // let host know we've tried to move here
                    WD.senddata(WD.ESCAPE + "J" + getpromptnum(promptid) + ".0");
                    sentdata = true;
                }
            }
            if (value == WD.ESCAPE + "?" && getpromptnum(promptid, true) != hostfocusprompt) {
                WD.senddata(WD.ESCAPE + "J" + getpromptnum(promptid, true));
                sentdata = true;
            }

            if (prompt.oldvalue === undefined) {
                prompt.oldvalue = "";
            }
            /*
             * TLB Handling
             * Get "??"/"?" before changed field value, so "??"/"?" ends up in dirtydata
             * Tested order in both Chrome and Edge, so far no difference
             */
            if (dirtydata == WD.ESCAPE + "?" || dirtydata == "?") {
                if (prompt.oldvalue != prompt.value) {
                    // Perform lookup against entered data
                    value = "?" + value;
                    dirtydata = null;
                } else {
                    // No new value, so leave dirtydata alone
                    return;
                }
            }
            // trying to handle clearing field
            if (value == "" && prompt.oldvalue != prompt.value && prompt.oldvalue != "") {
                value = " " + WD.AM;
            }
            if (jPrompt.parent().hasClass("nav-pills")) {
                var data = "WGUF:" + ((promptid.split("_")[0] - 500) % 1000) + ":" + getpromptnum(promptid) + ":" + value;
                WD.disablescreens();
                WD.senddata(data, true);
            } else {
                if (origvalue == value && !jPromptObj.data("dirty")) {
                    // don't send anything, from display command
                } else {
                    dirtydata = value;
                    if (jPrompt.parents(".multiselect, .showselect").length == 0) {
                        dirtydataprompt = getpromptnum(promptid, true);
                    } else {
                        dirtydataprompt = jPrompt.parents("tr").data("promptno") + "." + value;
                    }
                    if (!sentdata) {
                        setTimeout(WD.pushdirtydata, 250);
                    }
                }
            }
        },
        getjump: function(promptid) {
            var data = WD.ESCAPE + "J";
            data += getpromptnum(promptid, true);
            if (data.indexOf(".") == -1) {
                data += ".0";
            }
            return data;
        },
        focused: function(promptid) {
            // return true if we are the host focused element
            if (hostfocusprompt.toString().split(".")[0] == getpromptnum(promptid, false)) {
                return true;
            } else {
                return false;
            }
        },
        focuselement: function(e, promptid) {
            // send jump command to host
            // promptid is Screen_Prompt
            // only trust things which are user initiated - isTrustred in
            // Chrome/Firefox or
            // which if initiated from mouse/keyboard (all browsers)
            // ie: don't want focus() calls to send something to the host
            // console.log("Focus Element", promptid, sentdata);
            var jPrompt = $("#" + jQueryID(promptid));
            if (jPrompt.attr("click")) {
                // buttons issue an onfocus before onclick
                // don't want to send to packets to host in this case
                jPrompt.removeAttr("click");
                return;
            }

            var alreadyhasfocus = (hostfocusprompt == getpromptnum(promptid, true));
            var focusedelement = jPrompt.hasClass("focuselement");
            var data = null;
            var hasdirtydata = (dirtydata !== null);

            var jPromptGrid = WD.getgridfromprompt(jPrompt);
            
            /* In some cases itemqueue is being processed and focusevent is triggered simualtnously 
                (in that case focus event should force send otherwise data is not synced)*/
            var forcesend = !itemqueueprocessed && jPromptGrid && jPromptGrid.data("focusedgridrow") !== promptid;

            //console.log("focuselement sentdata="+ sentdata+ ", alttab=" +alttab);
            if ((!sentdata || forcesend) && (!alttab || !alreadyhasfocus)) {
                if (hasdirtydata) {
                    data = dirtydata;
                }
                dirtydata = null;
                dirtydataprompt = 0;
                //console.log("focuscheck", hostfocusprompt, getpromptnum(promptid, true), alreadyhasfocus, focusedelement);
                //console.log(e);
                if (!alreadyhasfocus && !focusedelement && e !== null) {
                    $(".focuselement").removeClass("focuselement");
                    if (data === null) {
                        data = "";
                    }
                    // clearing fields can add another AM
                    if (data !== "" && (typeof data === 'string' && data.search(WD.AM) == -1)) {
                        data += WD.AM;
                    }
                    if (WD.tab > 0) {
                        // console.log(promptid, WD.tab);
                        if (WD.tab == 2) {
                            data += WD.ESCAPE + "L";
                        } else {
                            data += WD.ESCAPE + "R";
                        }
                    } else if (!jPrompt.is("button,input[type=button]")) {
                        data += WD.getjump(promptid);
                    }
                }
                //console.log("data="+data);
            }

            // Dismiss active flash message, unless on button
            if (!alreadyhasfocus && !jPrompt.is("button")) {
                WD.cleartoast();
                if (jPrompt.parents("td").length > 0) {
                    // if in a grid, make sure we scroll into view
                    WD.scrollintoview(jPrompt.get(0));
                }
            }

            // remove class from previous element, add to us
            if (!alreadyhasfocus) {
                WD.unsetfocus();
            }
            jPrompt.addClass("focuselement");
            WD.applyscheme(jPrompt);
            if (jPrompt.length > 0) {
                var promptliteral = jPrompt.data("promptliteral");
                $("#promptliteral").html(promptliteral)
                    .attr("title", promptliteral);
            }
            var prompt = jPrompt.get(0);

            // Store Old Value
            if (prompt && prompt.type && (prompt.type.toLowerCase() !== "radio" && prompt.type.toLowerCase() !== "checkbox" && prompt.type.toLowerCase() !== "submit")) {
                prompt.oldvalue = prompt.value;
                prompt.select();
            } else if (jPrompt.is("iframe")) {
                // This was some bad code, not sure what the intention was
                // jPrompt.contentWindow.get
            }

            if (jPrompt.hasClass("manualprompt")) {
                WD.displaymanualprompt(jPrompt, true);
                return;
            }

            // don't send stuff if we were already on the prompt
            // console.log("focus", promptid, data, alreadyhasfocus, alttab);
            if (data != null && (!alreadyhasfocus || prompt.type.toLowerCase() == "radio" || prompt.type.toLowerCase() == "checkbox" || data.substr(0, 2) == (WD.ESCAPE + "?")) && !alttab) {
                //if (hasdirtydata) { WD.disablescreens(); }
                WD.disablescreens();
                WD.senddata(data);
                sentdata = true;
                // console.log("We should send data");
            }
            // reset tab key
            WD.tab = 0;
            alttab = false;
            searching = false;
            if (jPrompt.parents(".editgrid") && clicktimer) {
                clearTimeout(clicktimer);
                clicktimer = null;
            }

            if (jPromptGrid) {
                jPromptGrid.data("focusedgridrow", promptid);
            }
        },
        // Supress multiple single clicks
        // 500ms was too short, given the 450 delay we have before sending, increase to 750ms
        // Apply to whole table instead of just one row, clicking quickly across rows also confused the host
        ssclick: function(grid, row, send, dirty) {
            if (!processingevent($(grid).parents("table").get(0), "click", 750)) {
                WD.ssprocessclick(grid, row, send, dirty, true);
            }
        },
        ssdblclick: function(grid, row, send, dirty) {
            if (!processingevent(grid, "dblclick", 500)) {
                WD.ssprocessclick(grid, row, send, dirty, false);
            }
        },
        ssprocessclick: function(grid, row, send, dirty, singleclick) {
            var jgrid = $(grid);
            WD.showselect(jgrid, row, send, dirty);
            if (!singleclick) {
                // Send the doubleclick, clear any pending singleclick
                WD.sendrow(jgrid, row, send, dirty);
            } else {
                WD.input(WD.ESCAPE + "WDD" + WD.AM + "ROW" + WD.AM + jgrid.data("promptno") + WD.AM + row, true);
                if (send) {
                    // only show busy if this should be a send
                    WD.busy();
                }
                // Slap this in a timeout, want to handle double click vs single click in an appropriate fashion
                clicktimer = setTimeout(function() {
                    WD.sendrow(jgrid, row, send, dirty);
                }, 450);
            }
        },
        unsetfocus: function() {
            var element = $(".focuselement");
            element.removeClass("focuselement");
            element.data("dirty", false);
            // if focus element isn't active, but something else is
            // remove focus from it
            var currentel = document.activeElement;
            if (currentel !== element.get(0) && !$(currentel).is("iframe") && $(currentel).parents(".screen").length > 0) {
                if (hostfocusprompt != getpromptnum(currentel.id, true)) {
                    $(currentel).data("dirty", false);
                    document.activeElement.blur();
                }
            }
            return element;
        },
        highlightrow: function(currentrow, row) {
            tbody = currentrow.parent();
            tbody.find("tr").removeClass("sshighlight");
            currentrow.addClass("sshighlight");
            return currentrow;
        },
        showselect: function(currentrow, row, send, dirty) {
            // console.log("showselect", row, send);
            // unfocus any other prompt that had focus
            WD.unsetfocus();
            document.activeElement.blur();
            // remove any dirty data it may have set (can cause issues, AWD-1786)
            dirtydata = null;
            //  Set highlight on new row
            var selectrow = WD.highlightrow(currentrow, row);
            WD.scrollintoview(selectrow.get(0));
            WD.gridsetpromptliteral(selectrow);

            var disabledInput = selectrow.find("input[disabled]:first");

            if (document.activeElement.tagName.toUpperCase() === 'BODY') {
                $(".focuselement").removeClass("focuselement");
                disabledInput.addClass("focuselement");
            }

            return selectrow;
        },
        sendrow: function(selectrow, row, send, dirty) {
            // console.log("Selecting " + row, send, selectrow.data("promptno"), hostfocusprompt, tbody.parents(".multiselect").length, dirty);
            // process prompt
            var hostprompt = hostfocusprompt.toString().split(".")[0];
            // Let webdirect know what row is selected (for WC:QUERYROW)
            if (send !== null && send !== undefined && send) {
                if (dirtydata != null) {
                    dirtydata = null;
                    dirtydataprompt = 0;
                }
                WD.disablescreens();
                if (parseInt(selectrow.data("promptno")) !== parseInt(hostprompt)) {
                    // WinGem sends this as TWO packets, wtf
                    // WD has to send TWO packets too, with timeout set for 2nd packet, GC-349 
                    WD.input(WD.ESCAPE + "J" + selectrow.data("promptno") + "." + row);
                    setTimeout(function() {
                        WD.senddata(row);
                    }, 500);
                } else {
                    WD.senddata(row);
                }
            } else if (parseInt(selectrow.data("promptno")) !== parseInt(hostprompt) && (selectrow.parents("div.showselect") || (dirtydataprompt != 0 && dirtydataprompt != (hostprompt + "." + row)))) {
                WD.disablescreens();
                WD.senddata("J" + selectrow.data("promptno") + "." + row, true);
            } else if (dirty) {
                // don't think we need to set dirty at all
                // we do for show select grids on ok. SIGH.
                dirtydata = row;
                dirtydataprompt = selectrow.data("promptno");
            }
            if (clicktimer !== null) {
                clearTimeout(clicktimer);
                clicktimer = null;
            }
        },
        gridsetpromptliteral: function(row) {
            var firstitem = row.find("input").not("input[type=checkbox]").first();
            $("#promptliteral").html(firstitem.data("promptliteral"))
                .attr("title", firstitem.data("promptliteral"));
        },
        pushdirtydata: function() {
            // this gets queued up
            if (sentdata) {
                setTimeout(WD.pushdirtydata, 250);
            } else if (dirtydata != null) {
                // console.log("pushing dirty data",dirtydata);
                WD.disablescreens();
                var data = dirtydata + WD.AM;
                dirtydata = null;
                dirtydataprompt = 0;
                WD.senddata(data);
            }
        },
        about: function() {
            var $about = $("#about");
            if (!$about.length) {
                $("body").append("<div id='about'></div>");
                $('#about').on('hidden.bs.modal', function(e) {
                    $(".wdbg").get(0).style.zIndex = "-1";
                });
                $about = $("#about");
            }
            $about.load(sid + "/about", function() {
                $(".wdbg").get(0).style.zIndex = "1000";
                $about.children().first().modal();
            });
        },
        buttonclick: function(target, senddata, escapedata) {
            if (!screensdisabled) {

                if (senddata === "F2" && target.id) { 
                    // if button is ok and is clicked return focus to same input
                    var inputid = (target.id || "").split("_", 1)[0];
                    if (inputid) {
                        var prompts = document.querySelectorAll("input.prompt[required][id^='" + inputid + "'" );
                        var promptcount = prompts.length;
                        var counter = 0;
                        while (counter < promptcount) {
                            var prompt = prompts[counter];
                            if (!prompt.value) {
                                prompt.focus();
                                WD.displaytoast({msg: WD.loadstringliteral("IDS_WEBERR01")});
                                return;
                            }
                            counter+=1;
                        }
                    }
                }

                if (!processingevent(target, "click", 1000)) {
                    WD.cleartoast();
                    WD.senddata(senddata, escapedata);
                }
            }
        },
        menuclick: function(target, senddata, escapedata) {
            // make a seperate function in case we need to tweak numbers
            // seperately.
            // and also because JHO likes duplicating code.
            if (!screensdisabled) {
                if (!processingevent(target, "click", 500)) {
                    WD.senddata(senddata, escapedata);
                    WD.cleartoast();
                }
            }
        },
        senddata: function(data, escapedata) {
            // Sending input data
            if (escapedata !== null && escapedata !== undefined && escapedata) {
                data = WD.ESCAPE + data;
            }
            // turn ino compound packet
            if (dirtydata != null) {
                // don't do this if data is the same as dirtydata
                if (dirtydata != data && data !== "") {
                    data = dirtydata + WD.AM + data;
                }
                dirtydata = null;
                dirtydataprompt = 0;
            }
            WD.input(data);
        },
        busy: function() {
            // If busy is called again and removeClass was not removed clear the timeout (as busy would have corresponding ready function call)
            clearTimeout(waitingclasstimeoutid);
            $("body").addClass("waiting");
        },
        ready: function() {
            // in case there was an already ready function that was called earlier cancel it and reinit it
            clearTimeout(waitingclasstimeoutid);
            waitingclasstimeoutid = setTimeout(function() {
                $("body").removeClass("waiting");
            }, 300);
        },
        updateaclist: function(command) {
            var target = $("#" + jQueryID(command.name));
            if (target.length > 0) {
                target.empty();
                for (var i = 0; i < command.list.length; i++) {
                    var option = document.createElement("option");
                    option.value = command.list[i];
                    target.append(option);
                }
            }
        },
        selectfile: function(command) {
            if (command.origfile) {
                $("#origfile").removeClass('hidden');
                $("#originalfilename").html(command.origfile);
            } else {
                $("#origfile").addClass('hidden');
            }
            $("#targetfilename").html(command.targetfile);
            $("#retfilename").html(command.retfile);
            $("#filepicker").children().first().modal({
                show: true,
                keyboard: false,
                backdrop: 'static'
            });
            $("#fileupload").val(null);
            $("#upload").attr("disabled", true);
            $("#chosenfilenames").empty();
            $("#chosenfiles").addClass("hidden");
        },
        filechosen: function() {
            // A file was chosen
            /// console.log("filechosen", $("#fileupload").val());
            var filename = $("#fileupload").val().split('/').pop().split('\\').pop();
            $("#chosenfilenames").html("<span>" + filename + "</span><br/>");
            $("#chosenfiles").removeClass("hidden");
            if (filename !== "") {
                $("#upload").attr("disabled", false);
            }
        },
        uploadfile: function() {
            // upload given file
            var data = $('#fileupload');
            var filename = $('#targetfilename').html();
            var formData = new FormData();
            formData.append("upfile", data.get(0).files[0]);
            if (filename === "" && data.get(0).files[0]) {
                // get filename from file picker
                filename = data.get(0).files[0].name;
            }
            var retfilename = ($("#retfilename").html() == "true");
            if (retfilename) {
                // test
                formData.append("retfile", 1);
            }
            if (data.get(0).files[0]) {
                var successfunc = function(data, textStatus, xhr) {
                    //console.log("File uploaded", textStatus);
                    //WD.displaytoast({
                    //    msg: "File uploaded succesfully"
                    //});
                };
                WD.doupload(filename, formData, successfunc);
            } else {
                if (retfilename) {
                    WD.input(WD.ESCAPE + 'WHIR:');
                } else {
                    WD.input(WD.ESCAPE + 'WDF' + WD.AM + 'CANCEL');
                }
            }
        },
        doupload: function(filename, formData, callback) {
            $.ajax({
                url: sid + "/upload/" + encodeURIComponent(filename),
                type: 'POST',
                data: formData,
                cache: false,
                contentType: false,
                enctype: 'multipart/form-data',
                processData: false,
                success: callback
            });
        },
        cancelfileupload: function() {
            var retfilename = ($("#retfilename").html() == "true");
            if (retfilename) {
                WD.input(WD.ESCAPE + 'WHIR:');
            } else {
                WD.input(WD.ESCAPE + 'WDF' + WD.AM + 'CANCEL');
            }
        },
        input: function(data, fireandforget, skipdata, noenter) {
            // set flag to show that we are doing a request
            if (!fireandforget) {
                WD.busy();
            }
            var url = sid + "/input";
            if (!mainwindow) {
                url = approot + sid + "/input";
                if (isgc && window.opener) {
                    // Exclusions to the general rule of returning focus to the main window
                    var sendfocus = true;
                    if (data.search("csicmd:AIM-BROWSER") > -1) {
                        sendfocus = false;
                    }
                    if (data.search("csicmd:WO_FAVORITES") > -1) {
                        sendfocus = false;
                    }
                    if (sendfocus) {
                        window.open('', window.opener.name);
                    }
                }
                // report browsers don't have a socket, send data on the input path
                $.ajax({
                    url: url,
                    method: "POST",
                    data: {
                        in: data,
                        skipdata: 1,
                        noenter: (noenter ? 1 : 0)
                    }
                }).always(WD.ready.bind(this));
            }
            if (socket) {
                socket.emit("incoming", {
                    data: {
                        in: data,
                        session: sid,
                        noenter: (noenter ? 1 : 0)
                    }
                }, WD.ready.bind(this));
            }
        },
        startpoll: function() {
            // prevent sleeping tabs here
            if (mainwindow && !lockResolver) {
                if (navigator && navigator.locks && navigator.locks.request) {
                    const promise = new Promise((res) => {
                        lockResolver = res;
                    });
                    navigator.locks.request(sid, { mode: "shared" }, () => {
                        return promise;
                    });
                }
            }
            if (socket) {
                return;
            }
            if (!mainwindow || loggedout) {
                return;
            }

            if (!socketManager) {
            // Use SocketIO's socket manager to set base configuration for the socket
            // This allows us to control the rate of events.
            // And initiate manual reconnects
                var targeturl = window.location.origin;
                var socketiopath = window.location.pathname.replace("#", "");
                if (loginserver && socketiopath.indexOf("login/") > 0) {
                    socketiopath = socketiopath.substring(0, socketiopath.indexOf("login/"));
                }
                socketiopath += "socket.io/";
                // build socket manager that will attempt to reconnect every 1s
                // up until 300 attempts have been made (~5m)
                console.log("Target %s, path %s", targeturl, socketiopath);
                socketManager = new io.Manager(targeturl, {
                    reconnectionDelay: 1000,
                    reconnectionAttempts: 5 * 60,
                    query: {
                        "sessionid": sid
                    },
                    path: socketiopath
                });
            }

            // open socket from socket manager
            socket = socketManager.socket("/");
            socket.on("connect", function() {
                if (disconnected) {
                    // test that we are a valid connection
                    WD.testConnectionValid();
                }
                disconnected = null;
                connectionDelay = 0;
            });

            socket.on("disconnect", function(reason) {

                var errorMsg = "";
                var manualReconnect = false;
                // Log Errors Better, client errors from https://socket.io/docs/v3/client-socket-instance/#disconnect
                switch(reason) {
                    case "ping timeout":
                        errorMsg = "The server did not send a PING within the specified interval";
                        break;
                    case "transport close":
                        errorMsg = "The connection was closed (i.e connection lost or changed)";
                        break;
                    case  "transport error":
                        errorMsg = "The connection has encountered an error (server killed or some unexpected issue)";
                        break;
                    case "io server disconnect":
                        errorMsg = "The server has forcefully disconnected the socket";
                        manualReconnect = true;
                        break;
                    case "io client disconnect":
                        errorMsg = "The socket was manually disconnected by the client";
                        break;
                    default:
                        errorMsg = "Unexpected disconnect";
                }

                console.log(errorMsg);
                disconnected = Date.now();

                if (manualReconnect) {
                    // if the server disconnects, we need to do a manual check
                    // we may be in the weird case of host died, resumed and lost our session
                    // but we still think it's all good
                    WD.attemptReconnect();
                }
            });
            socket.io.on("reconnect_failed", () => {
                console.log("SocketIO could not reconnect automatically, falling bcak to manual attempt.")
                WD.attemptReconnect();
            });
            socket.on('connect_error', function() {
                console.log("Connection could not be established, attempting to reconnect.");
            });
            socket.on("data", function(msg, cb) {
                WD.processresponse(msg);
            });
        },
        attemptReconnect: function(delay) {
            // Manually reconnect the websocket
            // disable internal reconnect

            // destroy Websocket
            // there's some issues with letting it reconnect on it's own
            if (socket) {
                socket.disconnect();
            }
            socket = null;

            // Failed to establish connection to host
            var ERR_MSG = WD.loadstringliteral("IDS_WEBERR0007", "Connection lost, attempting to reconnect...");
            WD.displaytoast({
                msg: ERR_MSG,
                msgtype: "ERROR"
            }, false);

            if (disconnected) {
                // check how long it's been
                var timediff = Date.now() - disconnected;
                // allow for 15 minutes to reconnect
                // otherwise logout, host will already have removed the connection
                if (timediff > (15 * 60 * 1000)) {
                    WD.logout({
                        msg: "Exceeded 15m wait time for server response.",
                        msgtype: 'ERROR'
                    });
                }
            } else {
                disconnected = Date.now();
            }

            if (delay) {
                if (!reconnectTimer) {
                    // keep increasing the delay
                    connectionDelay += delay;
                    // max it at 1 minute
                    if (connectionDelay > 60 * 1000) {
                        connectionDelay = 60 * 1000;
                    }
                    console.log(" Restarting connection in %d", connectionDelay);
                    reconnectTimer = setTimeout(WD.restartConnection, connectionDelay);
                }
            } else {
                // restart our connection
                WD.restartConnection();
            }
        },
        restartConnection: function() {
            // clear timer
            clearTimeout(reconnectTimer);
            reconnectTimer = null;

            // determine if server is up or not
            $.ajax({
                url: "healthcheck"
            }).then(
                WD.connectionPending,
                WD.connectionfailure
            );
        },
        testConnectionValid: function() {
            $.ajax({
                url: sid + "/about"
            }).then(
                function(data, textStatus, jqXHR) {
                    // we are alive again, attempt connection
                    if (!socket) {
                        clearTimeout(reconnectTimer);
                        WD.startpoll();
                    }
                },
                WD.connectionfailure
            );
        },
        connectionPending: function(data, textStatus, jqXHR) {
            if (jqXHR.status == 200) {
        // server is up, check to see if our session
        // is still alive
                WD.testConnectionValid();
            } else {
                // health check didn't return a 200
                // something weird going on
                console.log("Health check returned %d", jqXHR.status);
                WD.attemptReconnect(10000);
            }
        },
        connectionfailure: function(xhr, status, errorThrown) {
            console.log("Connection failure %s (%s)", errorThrown, status);
            if (xhr.status == 403) {
                clearTimeout(reconnectTimer);
                WD.logout({
                    msg: "Session no longer valid.",
                    msgtype: 'ERROR'
                });
            } else {
                WD.attemptReconnect(10000);
            }
        },
        updateprogressbar: function(command) {
            // Status Bar display
            var pbholder = $("#progress");
            var pb = $("#progressbar");
            var pbl = $("#progresslabel");
            var modalwin = pbholder.children().first();
            var show = true;
            if (command.init) {
                pb.attr('aria-valuenow', 0);
                if (command.message) {
                    pbl.html(command.message);
                }
            } else if (command.close) {
                pb.css({
                    width: 0
                });
                pb.attr("aria-valuenow", 0);
                show = false;
            } else if (command.show) {} else if (command.hide) {
                show = false;
            } else if (command.update) {
                pb.attr("aria-valuenow", command.update);
                pb.css({
                    width: command.update + "%"
                });
            } else if (command.message) {
                pbl.html(command.message);
            }
            if (show) {
                modalwin.modal({
                    backdrop: 'static'
                    // this should be turned on once we are satisfied,
                    //keyboard: false
                });
            } else {
                modalwin.modal("hide");
            }
        },
        updatemenubar: function(command) {
            // console.log("updatemenubar", command);
            // menubar update
            menubar = $(".wdmenubar", wcontainer);
            switch (command.action) {
                case "ENABLE":
                case "SHOW":
                    menubar.find("li").removeClass("disabled");
                    menubar.show();
                    if (command.value) {
                        menubar.find(".active").removeClass("active");
                        var newval = menubar.find("[data-value='" + command.value + "']");
                        newval.addClass("active");
                        if (!newval.is(isdisplayed)) {
                            // maybe on "top" level
                            $(".submenubar").hide()
                                .siblings("ul").show();
                        }

                        if (newval && newval.length === 1) {
                            newval = newval[0];
                            setTimeout(function() {
                                if (newval) {
                                    newval.scrollIntoViewIfNeeded ? newval.scrollIntoViewIfNeeded() : newval.scrollIntoView();
                                }
                            }, 100);
                        }
                    }
                    WD.positionmenubar();
                    break;
                case "DISABLE":
                    menubar.find("li").removeClass("disabled");
                    break;
                case "HIDE":
                    menubar.hide();
                    break;
                case "SETFOCUS":
                    // This probably isn't good enough
                    WD.hostfocus(menubar.attr("id"), false);
                    menubar.trigger("focus");
                    break;
            }
        },
        positionmenubar: function(toitem, dragmove) {
            // reposition menubar (if needed and exists)
            var menubar = $(".wdmenubar", wcontainer);
            if (menubar.length > 0) {
                if (menubar.length > 1) {
                    menubar.first().remove();
                    menubar = $(".wdmenubar", wcontainer);
                }
                if (toitem && toitem.is(isdisplayed)) {
                    toitem = null;
                }
                if (!toitem) {
                    toitem = wcontainer.find(".screen").filter(isdisplayed).last();
                }
                // only move menubar if same execute level, and NOT a live menu bar
                // OR if live and parent window is not shown
                var sameexlevel = Math.floor(parseInt(menubar.data('screenid')) / 1000) >= Math.floor(parseInt(toitem.children('.reactscreen').data('screenid')) / 1000);
                var calldifference = parseInt(toitem.children('.reactscreen').data('screenid')) - parseInt(menubar.data('screenid'));
                var mbislive = (menubar.data("live") == "1");
                if (sameexlevel && calldifference < 2 && calldifference >= 0) {
                    if (!mbislive || calldifference == 0) {
                        menubar.insertAfter(toitem);
                    }
                    var toparent = toitem.prevAll(".screen").filter(isdisplayed).first();
                    var bottom = 0;
                    if (toparent.length > 0) {
                        bottom = toparent.data("endrow");
                    }
                    // console.log(mbislive, calldifference, dragmove);
                    // console.log(bottom, toitem.data("endrow"));
                    toitem = toitem.children(".reactscreen");
                    if (toitem.data("position") !== "FULLSCREEN" &&
                        ((calldifference == 0) ||
                            (!mbislive) ||
                            ((bottom == 0 || (bottom == toitem.data("endrow") && calldifference > 0 && !dragmove))) ||
                            (calldifference == 1 && mbislive && (!toitem.prevAll(".screen").first().is(isdisplayed))))
                    ) {
                        menubar.position({
                            my: "left top",
                            at: "left bottom",
                            of: toitem,
                            collision: "none"
                        });
                        menubar.css({
                            width: toitem.outerWidth()
                        });
                    } else {

                        var blockWindow = menubar.prevAll("#windowblock");
                        var draggableScreenAfterMenu = menubar.is(isdisplayed) ? blockWindow.nextAll(".screen.ui-draggable") : {};
                        
                        if (draggableScreenAfterMenu.length === 1 && draggableScreenAfterMenu.is(isdisplayed)) {
                            // If there is (single) visible dragabble window after menu, adjust menu as per the screen
                            var screenPosition = draggableScreenAfterMenu.position();

                            //menu should be exactly below the window i.e screen top + height
                            var menuTop = screenPosition.top + draggableScreenAfterMenu.height(); 

                            // menu should should be as left as the dragabble screen
                            menubar.css({top : menuTop, left: screenPosition.left});

                        } else {
                            // reset menubar to fullscreen position
                            // code from host can be wrong depending on screen flow and timing
                            menubar.css({
                                left: 0,
                                right: 0,
                                bottom: 0,
                                top: "",
                                width: "100%"
                            });
                        }
                    }
                }
            }

            if (menubar && menubar.length === 1 && menubar.is(".wdmenubar:visible")) {
                var menuchildren = menubar.children("ul");
                var isnooverflow = menuchildren.length === 1 && menubar.outerHeight() > menuchildren.outerHeight();
                
                if (menuchildren.length === 1) {
                    menubar.css("overflow-y", isnooverflow ? "" : "auto");
                }
            }
        },
        updatetext: function(command) {
            // This is just used to update a container with text rather than a
            // field in a screen
            // it can handle multiple targets all stacked within the target
            // property as an array
            $.each(command.target, function(index, value) {
                $(value).text(command.value[index]);
            });
        },
        fireevent: function(command, delayClicks) {
            //console.log("fireevent");
            var target = getiframe(command.targetid, true);
            if (target && target.length > 0) {
                var targetelement = target.find("#" + jQueryID(command.element) + ", [name='" + jQueryID(command.element) + "']");
                if (targetelement.length > 0) {
                    switch (command.event) {
                        case "CLICK":
                            if (delayClicks) {
                                clickqueue.push(targetelement);
                            } else {
                                targetelement.trigger("click");
                            }
                            break;
                        case "SUBMIT":
                            targetelement.trigger("submit");
                            break;
                        case "RESET":
                            targetelement.reset();
                            break;
                    }
                } else {
                    var bFoundInFrame = false;
                    var frames = target.find("frame");
                    for (var j = 0, len = frames.length; j < len; j++) {
                        var frame = frames[j];
                        targetelement = $(frame.contentDocument).find("#" + jQueryID(command.element) + ", [name='" + jQueryID(command.element) + "']");
                        if (targetelement.length > 0) {
                            bFoundInFrame = true;
                            switch (command.event) {
                                case "CLICK":
                                    if (delayClicks) {
                                        clickqueue.push(targetelement);
                                    } else {
                                        targetelement.trigger("click");
                                    }
                                    break;
                                case "SUBMIT":
                                    targetelement.trigger("submit");
                                    break;
                                case "RESET":
                                    targetelement.reset();
                                    break;
                            }
                        }
                    }
                    /*if (!bFoundInFrame) {
                        console.log("Could not find WFE/WFB element", command.element);
                    }*/
                }
            } else {
                // external browser that hasn't loaded, wait for it
                if (command.targetid in browsers) {
                    $(browsers[command.targetid]).on("load", function() {
                        WD.fireevent(command, false);
                    });
                }
                /* else {
                    console.log("Could not find WFE/WFB target", command.targetid);
                }*/
            }
        },
        updatebrowser: function(command) {
            //console.log("updatebrowser");
            var target = getiframe(command.targetid, true);
            if (target && target.length > 0) {
                var targetelement = target.find("#" + jQueryID(command.element) + ", [name='" + jQueryID(command.element) + "']");
                if (targetelement.length > 0) {
                    if (command.updatetype === "I") {
                        targetelement.get(0).innerHTML = command.html;
                    } else {
                        targetelement.get(0).outerHTML = command.html;
                    }
                } else {
                    var bFoundInFrame = false;
                    var frames = target.find("frame");
                    for (var j = 0, len = frames.length; j < len; j++) {
                        var frame = frames[j];
                        targetelement = $(frame.contentDocument).find("#" + jQueryID(command.element) + ", [name='" + jQueryID(command.element) + "']");
                        if (targetelement.length > 0) {
                            if (command.updatetype === "I") {
                                targetelement.get(0).innerHTML = command.html;
                            } else {
                                targetelement.get(0).outerHTML = command.html;
                            }
                        }
                    }
                    /*if (!bFoundInFrame) {
                        console.log("Could not find WUH/WUB element", command.element);
                    }*/
                }
            } else {
                // external browser that hasn't loaded, wait for it
                if (command.targetid in browsers) {
                    $(browsers[command.targetid]).on("load", function() {
                        WD.updatebrowser(command);
                    });
                }
                /* else {
                    console.log("Could not find WUH/WUB target", command.targetid);
                }*/
            }
        },
        closeallbrowsers: function() {
            for (var key in browsers) {
                if (browsers.hasOwnProperty(key) && browsers[key]) {
                    browsers[key].close();
                }
            }
            browsers = {};
        },
        externalbrowser: function(command) {
            // handle EBR packet data
            if (command.newwindow && command.newwindow == 1) {
                // console.log("ebr",command);
                if (command.tag === "ALL") {
                    WD.closeallbrowsers();
                    return;
                }
                var win = browsers[command.tag];
                if (command.cmd == "CLOSE") {
                    if (win) {
                        win.close();
                        delete browsers[command.tag];
                    }
                } else {
                    var targeturl = "";
                    // console.log(win, targeturl);
                    if (command.html == 1) {
                        targeturl = sid + "/external/" + command.url;
                    } else {
                        targeturl = command.url;
                    }
                    if (targeturl && targeturl != "") {
                        if (win != undefined && win != null && !win.closed) {
                            win.location = targeturl;
                            win.focus();
                        } else {
                            if (!command.realurl) {
                                if (loginserver && window.location.href.indexOf("login/") > 0) {
                                    targeturl = window.location.href.substring(0,window.location.href.indexOf("login/")).replace("#", "") + targeturl;
                                } else {
                                    targeturl = window.location.href.replace("#", "") + targeturl;
                                }
                            }
                            // determine if we are opening it somewhere instead of as tab
                            var specs = null;
                            if (command.left || command.top || command.width || command.height) {
                                specs = "";
                                // open in specific location
                                specs += "left=";
                                specs += (command.left ? (command.left * 10).toString() : "25");
                                specs += ",top=";
                                specs += (command.top ? (command.top * 8).toString() : "25");
                                specs += ",width=";
                                specs += (command.width ? (command.width * 10).toString() : "800");
                                specs += ",height=";
                                specs += (command.height ? (command.height * 8).toString() : "600");
                            }

                            if (command.cmd == "PRINT" || command.cmd == "PRINT-ASK") {
                                specs += ",noopener";
                                targeturl += "?action=print";
                            }

                            win = window.open(targeturl, command.tag, specs);

                            // This is supposed to be put focus back on main window
                            if (win) {
                                win.blur();
                                $(win).on("load", function() {
                                    if (command.title) {
                                        win.document.title = command.title;
                                    }
                                    window.focus();
                                });
                                browsers[command.tag] = win;
                            }
                        }
                    } else {
                        if (win) {
                            // this doesn't really do anything. :(
                            win.focus();
                        }
                    }
                }
            } else {
                WD.bgndbrowser(command);
            }
        },
        bgndbrowser: function(command) {
            // handle background browsers
            var promptObj = $("#" + jQueryID(command.targetid));
            var browser = promptObj.find("iframe").get(0);
            if (command.url && browser.src != command.url) {
                if (loginserver && window.location.href.indexOf("login/") > 0 && command.url !== 'about:blank') {
                    browser.src = "..\\" + command.url;
                } else {
                    browser.src = command.url;
                }
                promptObj.show().removeData("zorder");
            }
            if (command.zorder == "1") {
                // Move to back
                if (promptObj.data("zorder") !== undefined) {
                    promptObj.data("zorder", "1").hide();
                    // Show the next visible background browser in the stack, if any
                    $($("div.bgbrowser").get().reverse()).each(function() {
                        if ($(this).data("zorder") !== undefined && $(this).data("zorder") == "0") {
                            $(this).show();
                            return false;
                        }
                    });
                } else {
                    wcontainer.prepend(promptObj);
                    promptObj.data("zorder", "1");
                }
            } else if (command.zorder == "0") {
                // Bring to front
                if (promptObj.data("zorder") !== undefined) {
                    $(".bgbrowser").not("#WGBGB_1").hide();
                    promptObj.data("zorder", "0").show();
                } else {
                    if (wcontainer.children().last()[0] !== promptObj[0]) {
                        wcontainer.append(promptObj);
                    }
                    promptObj.data("zorder", "0");
                }
            }
            if (command.visible == true) {
                if (command.targetid == "WGBGB_1") {
                    if (isgc) {
                        wcontainer.css('left', promptObj.outerWidth() + $("#commandbarcontainer").outerWidth());
                    } else {
                        wcontainer.css('left', promptObj.css("width"));
                    }
                } else {
                    $(".bgbrowser").not("#WGBGB_1").hide();
                }
                var promptObjWindow = promptObj.find("iframe").get(0).contentWindow;
                var iframeActiveElement = promptObjWindow.document.activeElement;
                // show the browser
                promptObj.show();
                // try to focus the current/active element
                if (promptObjWindow.EDGE !== undefined) {
                    try {
                        promptObjWindow.EDGE.HTML1.focusCurrentElement();
                    } catch (e) {
                        if (iframeActiveElement !== null) {
                            iframeActiveElement.focus();
                        }
                    }
                } else {
                    if (iframeActiveElement !== null) {
                        iframeActiveElement.focus();
                    }
                }
            } else if (command.visible == false) {
                promptObj.hide();
                if (command.targetid == "WGBGB_1") {
                    if (isgc) {
                        wcontainer.css('left', $("#commandbarcontainer").outerWidth());
                    } else {
                        wcontainer.css('left', 0);
                    }
                }
            }
            if (command.width) {
                promptObj.css("width", command.width);
                if (isgc) {
                    wcontainer.css('left', command.width + $("#commandbarcontainer").outerWidth());
                } else {
                    wcontainer.css('left', command.width);
                }
            }
            WD.repositionblocker();
        },
        updatemailstatus: function(command) {
            var mailcont = $("#mailstatus");
            var mail = $("#mailimg");
            if (!command.visible) {
                // set it back to nothing if it's set to not visible.
                mailcont.html('<img class="buttonimage" id="mailimg">');
            } else {
                if (command.iconname !== "" && command.iconname != null) {
                    mail.attr("src", mailcont.data("basepath") + command.iconname);
                }
                // prefer custom messages if specified, otherwise just give
                // a number of unread / total
                if (command.message !== "" && command.message != null) {
                    mail.attr("title", command.message);
                } else if (command.unreadnum != "" && command.unreadnum != null) {
                    if (command.unreadnum > 1) {
                        mail.attr("title", "You have " + command.unreadnum + " mail messages.");
                    } else {
                        mail.attr("title", "You have " + command.unreadnum + " mail message.");
                    }
                }
                if (command.sendtype != "" && command.sendtype != null) {
                    carrret = String.fromCharCode(13);
                    // according to guicommand, sendtypes are W,E,& S.
                    // W means Windows command which im assuming is out of the
                    // question now.
                    // so check if it's E, assume S if not.
                    if (command.sendtype == "E") {
                        mail.attr("onclick", 'WD.senddata("' + command.sendtext + '",true);');
                    } else if (command.sendtype == "S") {
                        mail.attr("onclick", 'WD.senddata("' + command.sendtext + carrret + '",false);');
                    }
                }
                if (command.flash) {
                    mail.addClass("flash");
                }
            }
        },
        getinfo: function(command) {
            if (command.query == "browsers") {
                // return list of open sub-browsers
                // get background browsers
                var bgnd = document.querySelectorAll(".bgbrowser") || [];
                var bgndnames = "";
                var bgndurl = "";
                bgnd.forEach(function(elem) {
                    bgndnames += (bgndnames == "" ? "" : WD.SM) + elem.id;
                    bgndurl += (bgndurl == "" ? "" : WD.SM) + $(elem).find("iframe").attr("src");
                });
                var rptnames = "";
                for (var id in browsers) {
                    var valid = false;
                    try {
                        // closed is true if the window is not visible
                        // may not have been unloaded yet after user closes it
                        if (!browsers[id].closed) {
                            valid = true;
                        }
                    } catch (e) {
                        valid = false;
                    }
                    if (valid) {
                        rptnames += (rptnames == "" ? "" : WD.SM) + id;
                    } else {
                        // remove any closed windows
                        delete browsers[id];
                    }
                }
                var packet = WD.ESCAPE + 'WHIR:' + bgndnames + WD.VM + bgndurl + WD.VM + rptnames + WD.VM + rptnames;
                // console.log(packet);
                WD.input(packet, true);
            }
        },
        askquestion: function(command) {
            // ask user a question, return result to input
            var connectwin = $("#connectingdialog").children().first();
            var modalwin = $("#question").children().first();
            if (connectwin.is(":visible")) {
                modalwin.one('hidden.bs.modal', function() {
                    WD.showconnecting();
                });
                connectwin.modal("hide");
            }
            modalwin.find("#questionheader").html(command.header);
            modalwin.find("#questionlabel").html(command.label);
            modalwin.on('shown.bs.modal', function() {
                $("input,button", modalwin).trigger("focus");
            });
            var input = modalwin.find("#questioninput");
            input.val("");
            if (command.inputtype) {
                input.attr("type", command.inputtype);
            } else {
                input.attr("type", "text");
            }

            WD.showdraggablemodal(modalwin, {keyboard: false});
        },
        showdraggablemodal: function(modelelem, properties) {
            modelelem.modal(properties || {});
            modelelem.find(".modal-dialog").draggable({
                handle: ".modal-header"
            });
        },
        destroymodaldraggable: function(dialogbutton) {
            $(dialogbutton).parents(".modal-dialog").first().removeAttr("style").draggable("destroy");
        },
        showmessage: function(command) {
            // Add the buttons into the message box
            $("#messagecontainer .tbutton").remove();
            $.each(command.button, function(index, abutton) {
                var sbutton = $("#messagecontainer").find(".modal-footer button:first").clone();
                sbutton.text(abutton.buttonlabel).addClass('tbutton').removeClass('hidden');
                if (!abutton.nosend) {
                    sbutton.on("click", function(event) {
                        WD.input(WD.ESCAPE + abutton.returndata);
                    });
                }
                if (abutton.nosend && typeof abutton.callback === "function") {
                    sbutton.on("click", abutton.callback);
                }
                $("#messagecontainer .modal-footer").append(sbutton);
            });
            $("#messageicon").attr("src", $("#messageicon").data("basepath") + command.image);
            $("#popupmessagetext").html(command.msg);
            $("#msgtitle").text(command.header);
            var modalwin = $("#messagecontainer").children().first();
            modalwin.on('shown.bs.modal', function() {
                // console.log("modal shown");
                WD.unsetfocus();
                var focusbutton = modalwin.find("button.tbutton").first();
                hostfocusprompt = 0;
                focusbutton = focusbutton.length > 0? focusbutton : modalwin.find(".modal-footer > button");
                focusbutton.trigger("focus");
            });
            WD.showdraggablemodal(modalwin);
        },
        showconnecting: function() {
            // Show "progress" dialog during logon
            connecting = true;
            var modalwin = $("#connectingdialog").children().first();
            modalwin.modal({
                backdrop: 'static',
                keyboard: false
            });
        },
        doneconnecting: function() {
            if (connecting) {
                keepTCLhidden = false;
                WD.hideconnecting();
                $("#statusbar").show();
                WD.hidestart();
                connecting = false;
            }
        },
        hideconnecting: function() {
            // Hide logon "progress" dialog
            var modalwin = $("#connectingdialog").children().first();
            modalwin.modal('hide');
            $(".wdbg").hide();
            $("#logoutbutton").show();
        },
        repositionblocker: function() {
            var itemset = $(".bgbrowser").filter(isdisplayed).add(".screen, .menu").not("#WGBGB_1");
            var winblocker = $("#windowblock");
            winblocker.remove();
            winblocker = $("<div id='windowblock'></div>");
            var lastitem = itemset.eq(-2);
            if (lastitem.length == 0) {
                lastitem = itemset.last();
                winblocker.insertBefore(lastitem);
            } else {
                // console.log("moving window block", lastitem.attr("id"));
                winblocker.insertAfter(lastitem);
            }
            // This is all to get around MS Edge's inability to redraw things properly
            // for MS Edge, need to redraw screen?
            // This code causes AWD-1746, need to rework it
            /*
            itemset.last().insertAfter(winblocker);
            if (itemset.next(".wdmenubar").length > 0) {
                // redraw it
                $(".wdmenubar").insertAfter(itemset.last());
            }
            */

            // Some screens in case of AWD-2001 have no contents but only prompts still they are shown as empty panel with buttons only such window should be hidden
            setTimeout(function() {
                var screens = winblocker.siblings(".screen"); 
                screens.removeClass("invisiblepromptscreen");
                WD.hidewinblockedpromptscreen(screens);
            }, 200);
        },
        hidewinblockedpromptscreen: function(scrs) {
            // hide window which contains nothing
            scrs.each(function() {

                var elem = $(this);
                var currentscreen = elem.children(".subscreen");
                var screenelements = currentscreen.children();
                var nonemptyelems = screenelements.not(".manualprompt:hidden,button");
                
                if (nonemptyelems.length > 0) { // if there is an element, this is not manualprompt and rest do nothing
                    return;
                }
                
                var manualprompts = screenelements.filter(".manualprompt:hidden");

                if (manualprompts.length === 0) { // if no manualprompts do nothing
                    return;
                }

                var allBtns = screenelements.filter("button");

                if (allBtns.length === 0) { // no buttons do nothing
                    return;
                }

                if ((manualprompts.length + allBtns.length) !== screenelements.length) { //if only have manualprompts (hidden) and button, ignore it
                    return;
                }

                // hide such screen where there is nothing but only hidden prompts
                elem.addClass("invisiblepromptscreen");

            });

        },
        closecommand: function(command) {
            // console.log("Close Command", command);
                var screenstoremove = $(".screen", wcontainer).filter(function() {
                    // console.log(parseInt($(this).data("screenid")) >= parseInt(command.targetid), this);
                    return parseInt($(this).children(".reactscreen").data("screenid")) >= parseInt(command.targetid);
                });
                screenstoremove.each(function( index ) {
                    var container = $(this).get(0);
                    WDC.unmountComponentAtNode(container);
                    container.remove();
                });
                screens = screens.filter(function(screen) {return parseInt(screen.props.screenid) < parseInt(command.targetid)});
            switch (command.type) {
                case "CLOSESCREEN":
                    var objstoclose = $(".screen,.wdmenubar", wcontainer).filter(function() {
                        // console.log(parseInt($(this).data("screenid")) >= parseInt(command.targetid), this);
                        return parseInt($(this).children(".reactscreen").data("screenid")) >= parseInt(command.targetid);
                    });

                    // Check if a flash toash is attached to screen being closed, if yes close toast after some time
                    var tToast = $("#toast");
                    var screenattachedtotoast = tToast.data("screen-origin");

                    if (screenattachedtotoast) {
                        tToast.removeData("screen-origin");
                        var isscreenattachedtotoast =  objstoclose.filter("#" + screenattachedtotoast).length === 1;
                        if (isscreenattachedtotoast) {
                            globaltoasttimeout = setTimeout( function() { WD.cleartoast(); }, 5000 );
                        }
                    }

                    objstoclose.remove();

                    var menubar = $(".wdmenubar", wcontainer);
                    if (menubar.length > 0) {
                        WD.positionmenubar($(".screen", wcontainer).last());
                    }
                    $(".screen", wcontainer).last().find(".active").removeClass("active");
                    break;
                case "CLOSEMENU":
                    // closes both menus and screens
                    $(".menu,.wdmenubar", wcontainer).filter(function() {
                        // console.log($(this).data("menuid"),
                        // command.targetid);
                        return ($(this).data("menuid") >= command.targetid || $(this).data("screenid") >= command.targetid);
                    }).remove();
                    break;
            }
            // clear dirty data
            dirtydata = null;
            dirtydataprompt = 0;
            if (command.targetid == 0) {
                //hide all background browsers too
                $(".bgbgbrowser").hide();
                WD.cleartoast();
            }
            $(".screen", wcontainer).last().find("input,textarea.tempreadonly,button").prop("readOnly", false).removeClass("tempreadonly");
            WD.repositionblocker();
        },
        setmenubar: function(menubar, live, data) {
            // flip active
            jmenubar = $(menubar);
            // console.log("setmenubar",jmenubar.hasClass("disabled"));
            var siblingsdisabled = jmenubar.siblings('li.disabled');
            if (jmenubar.hasClass('disabled') || (jmenubar.hasClass("active") && siblingsdisabled.length > 0)) {
                return;
            }
            if (!live) {
                if (data) {
                    WD.senddata(data);
                }
                jmenubar.siblings('li').addClass("disabled").removeClass("active");
                jmenubar.addClass("active");
            } else if (data) {
                WD.updateelement(null, menubar, data);
            }
        },
        updateprompt: function(command) {
            // update a grid prompt (prompt literal)
            var promptObjs = getPromptObjects(command.targetid, true, true);
            var focusprompt = null;
            promptObjs.forEach(function(elem) {
                var jThis = $(elem);
                jThis.data("promptliteral", command.promptliteral);
                if (jThis.hasClass("focuselement")) {
                    // updatae prompt literal
                    $("#promptliteral").html(command.promptliteral)
                        .attr("title", command.promptliteral);
                }

                var jThisParent = jThis.parent();
                if (command.tlb) {
                    var clonedata = $(command.tlbicon ? "#tlbtemplate_icon" : "#tlbtemplate_button");
                    var newhtml = clonedata.html().replace(/default/g, jThis.attr("id"));
                    if (command.tlbicon) {
                        newhtml = newhtml.replace(/iconname/g, command.tlbicon);
                    }
                    
                    jThisParent.find(".wdtlb").remove();
                    jThisParent.append(newhtml);

                    var wdtlbInput = jThisParent.find(".wdtlb, input").removeClass("prompttlb");
                    if (command.tlbleft) {
                        wdtlbInput.addClass("tlbleft").removeClass("tlbright");
                    } else {
                        wdtlbInput.addClass("tlbright").removeClass("tlbleft");
                    }
                    wdtlbInput.addClass("prompttlb");

                    if (jThis.has(":focus")) {
                        // force draw of dropdown
                        focusprompt = jThis;
                    }
                } else {
                    jThisParent.find(".wdtlb").remove();
                }
            });
            if (focusprompt !== null) {
                focusprompt.trigger("focus");
            }
        },
        displayprompt: function(command, filteredprompt) {
            // Handle Prompt Updating
            var targetid = command.targetid;
            if (command.mvndx) {
                targetid += "_" + command.mvndx;
            }
            var promptObjs = filteredprompt ? filteredprompt[targetid] : getPromptObjects(targetid, false, true);
            var infocus = (command.focus && document.activeElement.getAttribute("name") === targetid) ? $(document.activeElement) : null;
            // console.log("Display", promptObjs.length);
            if (promptObjs && promptObjs.length > 0) {
                // need to know if they changed anything 
                if (infocus && command.hasOwnProperty("flash_msg_target") && command.flash_msg_target === targetid) {
                    // Fix For Clearing input on Road Service Screen
                    var screenInput = $(".screen:last input:not(:disabled)");
                    if (screenInput.length === 1  && screenInput[0].id === targetid) {
                        infocus = null;
                    }
                }   

                // do nothing for the codition met
                if (!(infocus && infocus.data("dirty"))) {

                    var dirtyitems;
                    if (command.focus) {
                        dirtyitems = document.querySelectorAll(".prompt");
                    }
                    
                    if (dirtyitems && dirtyitems.length > 0) {
                        // we need to reset these to their values, we either go too far ahead, 
                        // or entered bad data
                        dirtyitems.forEach(function(elem) {
                            var jElem = $(elem);
                            if (jElem.data('dirty')) {
                                elem = jElem.data("orig");
                            }  
                        });
                    }
                    // cleanup any bad input?
                    if (command.value !== null && command.value !== undefined) {
                        var screenid = targetid.split("_")[0];
                        if (screens[0].props.screenid = screenid) {
                            if (command.mvndx) {
                                screens[0].setGridValuefromHost(command.targetid,
                                    command.mvndx,
                                    command.value,
                                    command.bgcolour != "" ? "#" + command.bgcolour : "",
                                    command.textcolour != "" ? "#" + command.textcolour : "");
                            } else {
                                screens[0].setValuefromHost(targetid,
                                    command.value,
                                    command.bgcolour != "" ? "#" + command.bgcolour : "",
                                    command.textcolour != "" ? "#" + command.textcolour : "");
                            }
                        }
                    }
                }
            } else {
                // could be an iframe, which is based on ID
                var promptObj = getiframe(command.targetid, false);
                if (promptObj.is("iframe")) {
                    if (command.value !== undefined && command.value !== null) {
                        if (command.value !== "XXX") {
                            if (command.value === "") {
                                command.value = "static/blank.html";
                            }
                            // re-add this every time
                            promptObj.on("load", WD.updateiframefunctions(promptObj.get(0)));
                            if (loginserver && window.location.href.indexOf("login/") > 0 && command.value !== 'about:blank') {
                                promptObj.get(0).src = "..\\" + command.value;
                            } else {
                                promptObj.get(0).src = command.value;
                            }
                        }
                    }
                    if (command.focus) {
                        // Save current active element
                        var promptObjWindow = promptObj.get(0).contentWindow;
                        var iframeActiveElement = promptObjWindow.document.activeElement;

                        // Focus the iframe
                        promptObj.trigger("focus");
                        // Try to focus on current/active element
                        if (promptObjWindow.WDEDI !== undefined) {
                            if (iframeActiveElement !== null) {
                                iframeActiveElement.focus();
                            }
                        } else if (promptObjWindow.EDGE !== undefined) {
                            try {
                                promptObjWindow.EDGE.HTML1.focusCurrentElement();
                            } catch (e) {
                                if (iframeActiveElement !== null) {
                                    iframeActiveElement.focus();
                                }
                            }
                        } else {
                            if (iframeActiveElement !== null) {
                                iframeActiveElement.focus();
                            }
                        }
                    }
                }
            }
            if (command.focus) {
                var movefocus = !(infocus &&  infocus.data("dirty"));
                WD.hostfocus(targetid, movefocus);
            }
        },
        hostfocus: function(targetid, movefocus) {
            // console.log("Setting Focus", targetid);
            if (movefocus === undefined || movefocus === null) {
                movefocus = true;
            }
            hostfocusprompt = getpromptnum(targetid, true);
            if (movefocus) {
                WD.unsetfocus();
            }
            jPromptObj = getPromptObjects(targetid).first();
            if (jPromptObj.length == 0 && hostfocusprompt.indexOf(".") > 0) {
                screens[0].scrollToGridItem(hostfocusprompt);
                jPromptObj = getPromptObjects(targetid).first();
            }
            // we have a bit of weird case, where the prompt is text
            // but the checkbox is the prompt that stacks the data
            // so we need to handle this weird case
            var isCheckbox = jPromptObj.is(":checkbox") || jPromptObj.is(".checkboxlabel");
            if (dirtydataprompt != hostfocusprompt) {
                dirtydata = null;
                dirtydataprompt = 0;
            } else if (jPromptObj.is(":radio") || isCheckbox || (dirtydata && dirtydata.substr(0, 2) == (WD.ESCAPE + "?"))) {
                var data = dirtydata;
                dirtydata = null;
                dirtydataprompt = 0;
                WD.senddata(data);
            }
            // make sure screen is on (if it's the last screen and a browser is on top)
            var wcontainerbgsc = wcontainer.children(".screen,.bgbrowser,.menu").last();
            if (wcontainerbgsc.is(".bgbrowser")) {
                wcontainerbgsc.insertBefore(wcontainer.find(".screen").last());
                WD.repositionblocker();
            }
            // need to handle being in a select grid
            if (jPromptObj.length == 0) {
                // could be an iframe
                var promptObj = getiframe(targetid, false);
                if (promptObj.is("iframe")) {
                    if (movefocus) {
                        promptObj.addClass("focuselement").trigger("focus");
                        WD.focuselement(null, targetid);
                    }
                    hotkeys.setScope("screen");
                } else if (movefocus) {
                        // not on screen... uh, wtf?
                        var newfocus = $(".screen", wcontainer).last().find("button").not(".close,.wdtlb,:disabled").first();
                        newfocus.trigger("focus");
                }
            } else if (jPromptObj.parents("div.showselect").length > 0 && jPromptObj.is(":disabled")) {
                // console.log("in a row!", jPromptObj);
                // in a row!
                var row = jPromptObj.parents("tr");
                // index is zero based, show select expects 1 based
                // don't do dirty if multi-selects
                WD.scrollintoview(row.get(0));
                WD.ssprocessclick(row, row.parent().children().index(row) + 1, false, (row.parents(".multiselect").length == 0), true);
                var enabledInput = row.find("input:enabled").first();

                if (enabledInput.length > 0) {
                    enabledInput[0].focus();
                }
                
                alttab = false;

                hostfocusprompt = row.data("promptno");
                hotkeys.setScope("showselect");
            } else {
                // console.log("Setting Focus from Display");
                if (movefocus) {
                    jPromptObj.addClass("focuselement").trigger("focus");
                    WD.focuselement(null, targetid);
                }
                hotkeys.setScope("screen");
            }
        },
        displaymanualprompt: function(jPromptObj, focus) {
            var jManPrompt = $("#WD_manual_prompt").children().first();
            // Create the dialog from the prompt div
            var jPromptHtml = jPromptObj.html();
            jManPrompt.find(".modal-body").html(jPromptHtml);
            jManPrompt.find(".modal-title").html(jPromptObj.prop("title"));
            jManPrompt.find("button").data("promptid", jPromptObj.attr("id"));
            jManPrompt.on('shown.bs.modal', function() {
                hostfocusprompt = 0;
                $("#promptliteral").html(jPromptHtml).attr("title", jPromptHtml);

                if (jPromptObj.data("edittype") === "YORN" || jPromptObj.data("edittype") === "CONFIRM.Y") {
                    $(this).parent().find('button:nth-child(1)').trigger("focus");
                } else if (jPromptObj.data("edittype") == "NORY" || jPromptObj.data("edittype") === "CONFIRM.N") {
                    $(this).parent().find('button:nth-child(2)').trigger("focus");
                } else {
                    // Is it possible to have no default button
                }
            });
            if (focus) {
                WD.showdraggablemodal(jManPrompt, {
                    show: true,
                    keyboard: false,
                    backdrop: 'static'
                });
            }
        },
        scrollintoview: function(target) {
            var jTarget = $(target);
            var jParent = jTarget.parents("tbody").first();
            if (!WD.checkinview(jTarget, jParent, false)) {
                target.scrollIntoView();
            }
        },
        checkinview: function(elem, container, partial) {
            if (!elem) {
                return false;  // Add this check to handle undefined or null elem
            }
        
            var contHeight = container.height();
            var contTop = container.scrollTop();
            var contBottom = contTop + contHeight;
            var elemTop = elem.offset().top - container.offset().top;
            var elemBottom = elemTop + elem.height();
            var isTotal = (elemTop >= 0 && elemBottom <= contHeight);
            var isPart = ((elemTop < 0 && elemBottom > 0) || (elemTop > 0 && elemTop <= container.height())) && partial;
            
            return isTotal || isPart;
        },
        delayedtoast: function(command) {
            if (command && command.msg) {
                sessionStorage.setItem('message', command.msg);
                sessionStorage.setItem('msgtype', command.msgtype);
            }
        },
        displaytoast: function(command, notimeout) {
            // Toast Message Display
            var tToast = $("#toast").attr("style", "");
            tToast.removeData("screen-origin");
            tToast.find("#toastmessage").html(command.msg);

            var lastscreen = $(".screen:last", wcontainer);
            clearTimeout(globaltoasttimeout);
            // As in AFW, FLASH messages should not disappear after time
            if (command.msgtype == "FLASH") {
                notimeout = true;

                var lastscreenelem = lastscreen[0];
                if (lastscreen.length === 1 && lastscreenelem.id) {
                    tToast.data("screen-origin", lastscreenelem.id);
                }
            }
            var error = (command.msgtype == "ERROR");
            if (error) {
                tToast.removeClass("alert-warning");
                tToast.addClass("alert-danger");
                if (!notimeout) {
                    globaltoasttimeout = setTimeout(function() {
                        tToast.fadeOut("slow");
                    }, 25000);
                }
            } else {
                tToast.removeClass("alert-danger");
                tToast.addClass("alert-warning");
                if (!notimeout) {
                    globaltoasttimeout = setTimeout(function() {
                        tToast.fadeOut("slow");
                    }, 5000);
                }
            }
            var positioned = false;
            if (command.xpos && command.ypos) {
                // positions come in row/column values that are intended to equal em
                // from the following link, px are turned into em with this formula,
                // em = (px.width / parseFloat($("body").css("font-size"))
                // it's easy enough to reverse that into  em -> px
                // px = em.width * parseFloat($("body").css("font-size"))
                // http://stackoverflow.com/a/12241338
                bodyscale = parseFloat($("body").css("font-size"));
                if (isgc) {
                    xpx = ((command.xpos * bodyscale) + $("#commandbarcontainer").outerWidth() + tToast.width());
                    ypx = (command.ypos * bodyscale);
                } else {
                    xpx = ((command.xpos * bodyscale) + tToast.width());
                    ypx = ((command.ypos * bodyscale) + $("#commandbarcontainer").height());
                }
                tToast.position({
                    my: "right top",
                    of: wcontainer,
                    at: "left+" + xpx + " top+" + ypx,
                    collision: "fit",
                    within: wcontainer
                });
                positioned = true;
            }
            if (command.targetid) {
                targetprompt = $("#" + jQueryID(command.targetid));
                if (targetprompt.length > 0) {
                    // Use jqueryui's position to place it
                    tToast.position({
                        my: "left center",
                        of: targetprompt,
                        at: "right+10 center-10",
                        collision: "fit",
                        within: $("#windowcontainer")
                    });
                    positioned = true;
                }
            }
            if (!positioned) {
                var target = lastscreen;
                if (target.length == 0) {
                    target = $(".menu:last", wcontainer);
                }
                if (target.length == 0 && !isgc) {
                    target = $("#tcl").filter(":visible");
                }
                if (target.length == 0) {
                    target = wcontainer;
                }
                tToast.position({
                    my: "center top+1",
                    of: target,
                    at: "center top"
                });
            }
            tToast.fadeIn("slow");
        },
        // Dismiss active flash message
        cleartoast: function() {
            $("#toast").fadeOut("slow");
        },
        updateiframefunctions: function(iframe) {
            if ($(iframe).parents("#renderdata").length !== 0) {
                // don't apply this if we are in the render section
                return;
            }
            if (iframe && iframe.contentWindow && iframe.contentWindow.csi_navigate != WD.navigate) {
                // console.log($(iframe).data("browserid"),"overriding
                // functions", iframe.src);
                if (iframe.contentWindow.EDGE) {
                    // only do replace if Edge exists
                    iframe.contentWindow.EDGE.HTML1.post_to_url = WD.posttourl;
                    iframe.contentWindow.EDGE.HTML1.navigate = WD.navigate;
                } else {
                    // console.log("No edge in window");
                }
                // always override csi_navigate
                iframe.contentWindow.csi_navigate = WD.navigate;
                WD.overwritehref(iframe.contentWindow.document);
                for (var j = 0, len = iframe.contentWindow.frames.length; j < len; j++) {
                    $(iframe.contentWindow.frames[j]).on("load", function() {
                        WD.overwritehref(this.window.document);
                    });
                    iframe.contentWindow.frames[j].window.csi_navigate = WD.navigate;
                }
                WD.overwritesubmit(iframe.contentWindow.document);
                iframe.contentWindow.HTMLFormElement.prototype.submit = function() {
                    // console.log("prototype overridden!");
                    // Taken from here
                    // http://stackoverflow.com/a/33626279/110068
                    if (!$(this).data("submithandled")) {
                        WD.handlesubmit($(this));
                    }
                    return false;
                };
                if (iframe.parentNode.id) {
                    $(iframe.contentWindow.document).find("input,textarea,select").on("focus", function(e) {
                        var iframepromptno = getpromptnum(iframe.parentNode.id, false);
                        //console.log("input.focus hostfocusprompt="+hostfocusprompt.toString()+", iframepromptno="+iframepromptno)
                        if (iframepromptno > 0 && hostfocusprompt != iframepromptno) {
                            WD.focuselement(e, iframe.parentNode.id);
                        }
                    });
                }
                setTimeout(
                    function() {
                        WD.updateiframefunctions(iframe);
                    },
                    100);
            } else {
                // console.log($(iframe).data("browserid"),"not overriding
                // functions", iframe.src);
            }
        },
        overwritehref: function(doc) {
            $(doc).on("click", "a[href^='CSICMD'],a[href^='csicmd']", function(event) {
                event.preventDefault();
                var href_val = $(this).attr("href");
                WD.navigate(href_val);
            });
        },
        convertserializetolatin1: function(data) {

            var params = (data || "").split("&").reduce(
                function(paramsstr, currentparam) {
                    currentparam = currentparam.split("=");
                    var currentparamval = decodeURIComponent(currentparam[1]);
                    var encodedparam = currentparam[0] + "=" + WD.encodeLatin1URIComponent(currentparamval);
                    return paramsstr + (paramsstr? "&":"") + encodedparam;
                }, ''
            );

            return params;

        },
        handlesubmit: function(jform) {
            // console.log("override of submit");
            var data = WD.convertserializetolatin1(jform.serialize());
            var cmd = jform.attr("action");
            // get originating item (need to use indirect references)
            var src = jform.parentsUntil("window").parent().find("[wdclicked]");
            // console.log(src);
            if (src.length > 0) {
                data += "&" + src.attr("name") + "=" + src.val();
            }
            // console.log("form submit", cmd, data);
            $(this).data("submithandled", false);
            WD.navigate(cmd + "?" + data);
            //WD.input(WD.ESCAPE + cmd.replace("CSICMD", "csicmd") + "?" + data, true);
        },
        overwritesubmit: function(doc) {
            $(doc).on("click keypress", ":button,:submit", function(event) {
                // console.log("click or keypress on button!");
                $(":button,:submit").removeAttr("wdclicked");
                $(this).attr("wdclicked", 1);
            });
            $(doc).on("submit", "form[action^='csicmd'],form[action^='CSICMD']", function(event) {
                $(this).data("submithandled", true);
                WD.handlesubmit($(this));
                return false;
            });

        },
        posttourl: function(path, params) {
            // replaces the EDGE.HTML1.postToWingem function
            if (path.substr(0, 6).toUpperCase() == "CSICMD") {
                // var navigatePath = path + "?" + $.param(params) // replaces jquery $.param to have latin-1 support
                var navigatePath = path + "?" + WD.paramlatin1(params);
                WD.navigate(navigatePath);
                //WD.input(WD.ESCAPE + path.replace("CSICMD", "csicmd") + "?" + $.param(params), true);
            } else {
                // ?? what should we do in the non-csicmd case?
            }
        },
        paramlatin1: function(params) {
            // Method to convert params dictionary to latin 1

            if (!params) {
                return "";
            }

            params_str = "";

            for (var current_param_key in params) {
                // process values that are keys of the object
                if (params.hasOwnProperty(current_param_key)) {
                    var current_param = params[current_param_key] || "";
                    params_str += (params_str ? "&" : "") +  current_param_key + "=" + WD.encodeLatin1URIComponent(current_param);

                }
            }

            return params_str;

        },
        encodeLatin1URIComponent: function(inputStr) {

            // list of chars that need to be added to param_string_list (it is a temporary list)
            var param_string_list = [];
            var charlist = [];

            var inputStrLen = (inputStr || "").length;
            var inputCharIndex = 0;

            while(inputCharIndex < inputStrLen) {

                var inputChar = inputStr[inputCharIndex];
                var charcode = inputChar.charCodeAt(0);
                
                // latin 1 has unique scheme for chars >128 and <256 only
                if (charcode < 128 || charcode > 255 ) {
                    charlist.push(inputChar);
                } else  {
                    var charliststr = encodeURIComponent( charlist.join("") );

                    // convert character to latin 1
                    var char_mod = charcode % 16;

                    // This is same as dividing by 16
                    var char_base = (charcode - char_mod) >> 4;

                    // if base is greater than 9 then replace it with hex represention of number i.e 10 (ascii : 10-9 +64 = 65) = A, 
                            // if base is greater than 9 then replace it with hex represention of number i.e 10 (ascii : 10-9 +64 = 65) = A, 
                    // if base is greater than 9 then replace it with hex represention of number i.e 10 (ascii : 10-9 +64 = 65) = A, 
                    if (char_base > 9) {
                        char_base = String.fromCharCode((char_base - 9) + 64);
                    }

                    if (char_mod > 9) {
                        char_mod = String.fromCharCode((char_mod - 9) + 64);
                    }

                    // add string to param list
                    param_string_list.push( charliststr + "%" + String(char_base) + String(char_mod) );

                    charlist = [];
                }

                inputCharIndex++;

            }


            if (charlist && charlist.length > 0) {
                param_string_list.push(encodeURIComponent( charlist.join("") ));
            }

            return param_string_list.join("");

        },
        navigate: function(tmpURL) {
            // console.log("navigate!", tmpURL);
            // replaces the EDGE.HTML1.navigate function,
            // which assumes a full url
            WD.input(WD.ESCAPE + tmpURL.replace("CSICMD", "csicmd"), true, true);
        },
        receiveMessage: function(event) {
            // Do we trust the sender of this message?
            // do we require similar origin?
            // if (event.origin !== "http://example.com:8080")
            if (event.data && event.data.substr) {
                var start = event.data.substr(0, 7).toLowerCase();
                if (start == "csicmd:" || start == "csicmd?") {
                    // push data to host as csicmd:
                    WD.navigate("csicmd:postdata?" + event.data.substr(7));
                }
            }
        },
        resizeTextarea: function(t) {
            var scrollHeight = t.scrollHeight;
            var selectionStart = t.selectionStart;
            var selectionEnd = t.selectionEnd;
            var offset = t.offsetHeight - t.clientHeight;
            
            $(t).css('height', 'auto').css('height', scrollHeight + offset)
                .prop({"selectionStart": selectionStart, "selectionEnd" : selectionEnd});
        },
        saveLoginInfo: function() {
            setCookie("server", $("#server").val(), 30);
            setCookie("account", $("#account").val(), 30);
        },
        checkForMFA: function(value) {
            var serversWithMFA = $("#mfaservers").html();
            if (serversWithMFA.search("," + value + ",") >= 0) {
                $("#mfa").removeClass("hidden");
            } else {
                $("#mfa").addClass("hidden");
            }
        },
        onServerChange: function() {
            accountElement = $("#account");
            if (wdallowfree) {
                accountElement.attr("list", "accounts-" + this.value);
            } else {
                var sourceHTML = "";
                var sourceElement;
                // jQuery selectors don't like the periods in IDs
                // not standard anyway and should probably be fixed at some
                // point
                sourceElement = $("#" + jQueryID("accounts-" + this.value));
                if (sourceElement) {
                    sourceHTML = sourceElement.html();
                }
                accountElement.html(sourceHTML);

                // Enable account prompt if more than one choice, else disable
                if (accountElement.children().length <= 1 && accountElement.prop("nodeName").toUpperCase() == "SELECT") {
                    accountElement.prop("disabled", true);
                } else {
                    accountElement.prop("disabled", false);
                }
            }
        },
        changeTerminalSize: function(cols, rows) {
            // change terminal size
            tclcols = cols;
            tclrows = rows;
            if ($(".screen,.menu", wcontainer).length == 0) {
                // TCL
                WD.input("TERM " + cols + "," + rows);
            } else {
                // Window/Menu
                WD.input(WD.ESCAPE + "CSITERM:" + cols + "," + rows);
            }
            setTerminalSize();
        },
        printterm: function() {
            var termoutput = "";
            // each char is painfully it's own array so the only element
            // within that we care about is the 2nd([1]) and we have to build
            // them all into a string on their natural lines.
            var buffer = terminal.buffer.normal;
            for (var i = 0; i < buffer.length; i++) {
                var line = buffer.getLine(i);
                var termline = line.translateToString();
                termline = termline.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                termoutput += termline + "<br />";
            }
            // create window to put output in
            var twin = window.open();
            twin.document.write("<html><head><title>" + WD.loadstringliteral("IDS_CAP0118") + "</title>");
            twin.document.write("</head><body><pre>" + termoutput + "</pre></body></html>");
            // stop spinning
            twin.document.close();
            // scroll to end 
            twin.document.scrollingElement.scrollTop = twin.document.scrollingElement.scrollHeight;
        },
        textareaKeyHandler: function(e) {
            // don't create newlines in textareas
            if (e.keyCode === 10 || e.keyCode === 13) {
                e.preventDefault();
                var elem = $(e.target);
                elem.data("dirty", true).trigger("change");
                return false;
            }
        },
        applyscheme: function(context) {
            // loops through stored styles and applies them when invoked
            if (context) {
                context = context.parent();
            }
            $.each(schemesettings, function(index) {
                var telement = schemesettings[index].element;
                var tcolour = schemesettings[index].colour;
                var tarea = schemesettings[index].area;
                
                if (tcolour === undefined) {
                    return; // background colors of some are replaced by undefined style of focus element
                }
                if (tarea === "TEXT" || tarea === "SHOWFIELD" || tarea === 'EDITABLE' || tarea === 'FOCUS') {
                    return; // handled by react
                }

                $(telement, context).not(".bgcoloured").css("background-color", tcolour);
            });
        },
        viewLogs: function() {
            // the route for getting the log file download doesnt like to work with the
            // ajax call - it returns data but not as a nice automagic download :(
            // window closes anyways after the fact so nothing is really kicking around
            // that shouldnt be
            window.open(approot + sid + "/getlog");
        },
        toggleLogs: function() {
            $.ajax({
                url: sid + "/togglelog",
                success: function(loggingEnabled, status, jqxhr) {
                    var $tool = $("#COMMANDBAR_BAND_bndToolbarDebugCOMMANDBAR_TOOL_attEnable_Log img");
                    if ($tool.length) {
                        var src = $tool.attr("src");
                        var title = $tool.attr("title");

                        var $parent = $tool.parent();
                        var contents = $parent.contents();

                        var enableLogStr = WD.loadstringliteral("IDS_CAP0142");
                        var disableLogStr = WD.loadstringliteral("IDS_WEB0003", "Disable Log");

                        if (loggingEnabled) {
                            // was off, now flipped on
                            title = disableLogStr;
                            src = src.replace("log_start.svg", "log_stop.svg");
                            $parent.html(contents.slice(0, 2)).append(contents[2].textContent.replace(enableLogStr, disableLogStr));
                        } else {
                            // was on, now flipped off
                            title = enableLogStr;
                            src = src.replace("log_stop.svg", "log_start.svg");
                            $parent.html(contents.slice(0, 2)).append(contents[2].textContent.replace(disableLogStr, enableLogStr));
                        }
                        $tool.attr("src", src);
                        $tool.attr("title", title);
                        $tool.attr("alt", title);
                    }
                }
            });
        },
        sendContextHelp: function() {
            if (hotkeys.getScope() == "menu-selected") {
                var selmenu = $(".menu", wcontainer).last().find(".menuitem.selected");
                WD.input("?" + selmenu.attr("id"), false);
            } else {
                WD.input(WD.ESCAPE + "F1", true);
            }
        },
        /**
         * Initializes and loads editor which has been opened in its own window
         * @param {string} uriMod - URI to modified copy of file (new)
         * @param {string} uriOrig - URI to original copy of file (old)
         */
        standaloneeditorinit: function(type, uriMod, uriOrig) {
            setupEditor();
            require(['vs/editor/editor.main'], function() {
                if (type == "DIFF") {
                    loadDiffEditorContent(uriOrig, uriMod, "");
                } else {
                    loadEditorContent(uriOrig, "", true);
                }

            });
        },
        nextdiff: function() {
            diffnav.next();
        },
        prevdiff: function() {
            diffnav.previous();
        },
        beforeprint: function() {
            var iFrame = $("#externalsource");
            if (iFrame.length > 0) {
                var externalprintsource = document.getElementById("externalsource_print");
                externalprintsource.innerHTML = "";
                if (iFrame.get(0).contentWindow.frames.length > 0) {
                    // some of our report browsers may have framesets...
                    var subframes = iFrame.get(0).contentWindow.frames;
                    for (var i = 0; i < subframes.length; i++) {
                        if (subframes[i].name.toLowerCase() == "csimain") {
                            var localcss = WD.getallcss(subframes[i].document);
                            externalprintsource.innerHTML += ("<style>" + localcss + "</style>");
                            externalprintsource.innerHTML += subframes[i].document.body.innerHTML;
                        }
                    }
                } else {
                    // just dump the regular stuff                                                       
                    var internalcss = WD.getallcss(iFrame.get(0).contentWindow.document);
                    WD.getalllinks(iFrame.get(0).contentWindow.document);
                    externalprintsource.innerHTML += "<style>" + internalcss + "</style>";
                    externalprintsource.innerHTML += iFrame.get(0).contentWindow.document.body.innerHTML;
                }
            }
        },
        getallcss: function(doc) {
            var css = "", //variable to hold all the css that we extract
                styletags = doc.getElementsByTagName("style");
            //loop over all the style tags
            for (var i = 0; i < styletags.length; i++) {
                css += styletags[i].innerHTML; //extract the css in the current style tag
            }
            return css;
        },
        getalllinks: function(doc) {
            var head = document.getElementsByTagName('HEAD')[0];
            var alllinks = doc.getElementsByTagName("link");
            //loop over all the links
            for (var i = 0; i < alllinks.length; i++) {
                // Create new link Element 
                link = document.createElement('link');
                link.rel = 'stylesheet';
                link.type = 'text/css';
                link.href = alllinks[i].getAttribute("href");
                // Append link element to HTML head 
                head.appendChild(link);
            }
        },
        setlanguageobject : function(langObj) {
            /* Language object have additional characters in it & that are being used for specific purposes, we don't require it here
                Create a map out of it and remove additional characters
            */
           for (var objKey in langObj) {

            // Check if it is key rather than prototype property
            if (langObj.hasOwnProperty(objKey)) {
                var langVal = WD.es5trim(langObj[objKey]).replace(/\u0026/g, "");
                languageObject[objKey] = langVal;
            }

           }

        },
        loadstringliteral: function(resourceId, defaultValue) {
            // search languageObject for the resource, if not found use defaultValue
            return languageObject[resourceId] || defaultValue || "";
        },
        es5trim: function (inputStr) {
            inputStr = inputStr || "";
            // if trim exist on string use it else use regex to do this
            return  inputStr.trim ? inputStr.trim() : inputStr.replace(/^\s*(.*)\s*$/,"$1");
        },
        getgridfromprompt: function(jPrompt) {

            var promptid = jPrompt.attr('id');
            var jPromptGrid;
            if (promptid && jPrompt.hasClass("gridprompt") && !jPrompt.is(":disabled")) {
                var promptrootid = promptid.split("_", 1)[0];
                jPromptGrid = jPrompt.parents('[id^="' + promptrootid + '"].editgrid.showselect');
            }

            return jPromptGrid && jPromptGrid.length > 0 ? jPromptGrid: null; 

        }
    };
}();