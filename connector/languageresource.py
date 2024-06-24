""" String literals for english and french """
# pylint:disable=line-too-long

_STRING_MAP = {
    "en": {
        "IDS_CAP0001": "OK",
        "IDS_CAP0002": "&About",
        "IDS_CAP0003": "About",
        "IDS_CAP0004": "&Apply",
        "IDS_CAP0005": "&Cancel",
        "IDS_CAP0006": "Cancel",
        "IDS_CAP0007": "&Confirm:",
        "IDS_CAP0008": "&Customize...",
        "IDS_CAP0009": "&Delete",
        "IDS_CAP0010": "&Edit",
        "IDS_CAP0011": "&Host Name",
        "IDS_CAP0012": "Host Name:",
        "IDS_CAP0013": "&OK",
        "IDS_CAP0014": "Undock",
        "IDS_CAP0015": "&Password:",
        "IDS_CAP0016": "&Save As...",
        "IDS_CAP0017": "&Setting:",
        "IDS_CAP0018": "&System Info...",
        "IDS_CAP0019": "&User ID:",
        "IDS_CAP0020": "50% Complete",
        "IDS_CAP0021": "Accoun&t:",
        "IDS_CAP0022": "Account",
        "IDS_CAP0023": "Application",
        "IDS_CAP0024": "Command Line",
        "IDS_CAP0025": "Connecting to",
        "IDS_CAP0026": "Connection",
        "IDS_CAP0027": "Edit Setting",
        "IDS_CAP0028": "Entry",
        "IDS_CAP0029": "Information",
        "IDS_CAP0030": "Logon",
        "IDS_CAP0031": "Menu Path",
        "IDS_CAP0032": "Message",
        "IDS_CAP0033": "Decoded",
        "IDS_CAP0034": "Preparing file for decoding...",
        "IDS_CAP0035": "Question",
        "IDS_CAP0036": "Report",
        "IDS_CAP0037": "S&etting:",
        "IDS_CAP0038": "Sc&ript:",
        "IDS_CAP0039": "Script",
        "IDS_CAP0040": "Screen Capture",
        "IDS_CAP0041": "Script Query",
        "IDS_CAP0042": "Scripting Event Form",
        "IDS_CAP0043": "Starting Script...",
        "IDS_CAP0044": "The number of columns has been adjusted to",
        "IDS_CAP0045": "The number of rows has been adjusted to",
        "IDS_CAP0046": "This application requires at least 800 x 600 resolution.",
        "IDS_CAP0047": "Translator",
        "IDS_CAP0048": "Version",
        "IDS_CAP0049": "Warning: This computer program is protected by copyright law and international treaties. Unauthorized reproduction or distribution of this program, or any portion of it, may result in severe civil and criminal penalties, and will be prosecuted to the maximum extent possible under the law.",
        "IDS_CAP0050": "Dock Left",
        "IDS_CAP0051": "&Session",
        "IDS_CAP0052": "&Window",
        "IDS_CAP0053": "&Help",
        "IDS_CAP0054": "Standard",
        "IDS_CAP0055": "Up",
        "IDS_CAP0056": "&Print...",
        "IDS_CAP0057": "&Capture",
        "IDS_CAP0058": "&View",
        "IDS_CAP0059": "&Command Line...",
        "IDS_CAP0060": "Support Tools",
        "IDS_CAP0061": "Log",
        "IDS_CAP0062": "Monitor Command Line View",
        "IDS_CAP0063": "&Disable Disconnect",
        "IDS_CAP0064": "E&xit",
        "IDS_CAP0065": "NOT USED",
        "IDS_CAP0066": "Print Screen",
        "IDS_CAP0067": "Close",
        "IDS_CAP0068": "Back",
        "IDS_CAP0069": "Forward",
        "IDS_CAP0070": "Copy",
        "IDS_CAP0071": "Refresh",
        "IDS_CAP0072": "Find",
        "IDS_CAP0073": "Zoom",
        "IDS_CAP0074": "AXIS &Help",
        "IDS_CAP0075": "GoldCare &Help",
        "IDS_CAP0076": "View License Agreement",
        "IDS_CAP0077": "View Requirements and Enhancements/Bug Fixes",
        "IDS_CAP0078": "Circular Log",
        "IDS_CAP0079": "&Font...",
        "IDS_CAP0080": "Queued events have been processed.",
        "IDS_CAP0081": "No Command Line Activity",
        "IDS_CAP0082": "Command Line Activity",
        "IDS_CAP0083": "Command Line Activity - Input Required",
        "IDS_CAP0084": "&Default Font",
        "IDS_CAP0085": "Line: ",
        "IDS_CAP0086": "Port: ",
        "IDS_CAP0087": "SSL Secured (",
        "IDS_CAP0088": " Bit)",
        "IDS_CAP0089": "Security Alert",
        "IDS_CAP0090": "SSL Certificate:",
        "IDS_CAP0091": "Issued to:",
        "IDS_CAP0092": "Issued by:",
        "IDS_CAP0093": "Valid from:",
        "IDS_CAP0094": "Valid to:",
        "IDS_CAP0095": "&Yes",
        "IDS_CAP0096": "&No",
        "IDS_CAP0097": "Information you exchange with this server cannot be viewed or changed by others.  However, there is a problem with the server's security certificate.",
        "IDS_CAP0098": "Do you want to proceed with this connection anyway?",
        "IDS_CAP0099": "Secure connection (SS&L)",
        "IDS_CAP0100": "Certificate",
        "IDS_CAP0101": "Information you exchange with this server cannot be viewed or changed by others.\n\n- The certificate was issued by a trusted authority\n- The certificate date is valid\n- The certificate has a valid name",
        "IDS_CAP0102": "Copy",
        "IDS_CAP0103": "Decrease Font Size",
        "IDS_CAP0104": "Increase Font Size",
        "IDS_CAP0105": "Paste",
        "IDS_CAP0106": "Enhanced Transfer",
        "IDS_CAP0107": "Regular Transfer",
        "IDS_CAP0108": "Fall-back to Regular Transfer",
        "IDS_CAP0109": "A report containing specific support information about your ",
        "IDS_CAP0110": " session and computer resources has been created.",
        "IDS_CAP0111": "View the contents of this report",
        "IDS_CAP0112": "Open the folder containing the report",
        "IDS_CAP0113": "Session and System Info",
        "IDS_CAP0114": "Support Data Folder",
        "IDS_CAP0115": "A report containing details of this error has been created.",
        "IDS_CAP0116": "C&ancel",
        "IDS_CAP0117": "&Up",
        "IDS_CAP0118": "Command Line Contents",
        "IDS_CAP0119": "Top",
        "IDS_CAP0120": "Page Up",
        "IDS_CAP0121": "Scroll Up",
        "IDS_CAP0122": "Scroll Down",
        "IDS_CAP0123": "Page Down",
        "IDS_CAP0124": "Bottom",
        "IDS_CAP0125": " (Shared)",
        "IDS_CAP0126": "&New",
        "IDS_CAP0127": "Save Setting As...",
        "IDS_CAP0128": "Name:",
        "IDS_CAP0129": "Shared setting",
        "IDS_CAP0130": "Save As",
        "IDS_CAP0131": "Display ",
        "IDS_CAP0132": " Rows",
        "IDS_CAP0133": " Columns",
        "IDS_CAP0134": "Switch to ",
        "IDS_CAP0135": "Caps Lock is on",
        "IDS_CAP0136": "Login",
        "IDS_CAP0137": "Connecting to server...",
        "IDS_CAP0138": "Connecting...",
        "IDS_CAP0139": "Login",
        "IDS_CAP0140": "Password",
        "IDS_CAP0141": "User ID",
        "IDS_CAP0142": "Enable Log",
        "IDS_CAP0143": "View Log",
        "IDS_CAP0144": "Lookup",
        "IDS_CAP0145": "Mail",
        "IDS_CAP0146": "&Commands",
        "IDS_CAP0147": "Authentication Code",
        "IDS_ERROR0001": "is not an allowed link.  No action will be taken.",
        "IDS_ERROR0002": "Information not sent.  Packet size exceeds safe maximum.",
        "IDS_ERROR0003": "Links outside of this document are not allowed.  No action will be taken.",
        "IDS_ERROR0004": "Navigation Canceled",
        "IDS_ERROR0005": "Navigation Error",
        "IDS_ERROR0006": "The application was unable to change the default settings of the specified printer.",
        "IDS_ERROR0007": "Transmission Error",
        "IDS_ERROR0008": "You are not allowed to add words to the dictionaries.",
        "IDS_ERROR0009": "You may only add words to the",
        "IDS_ERROR0010": "dictionary.",
        "IDS_ERROR0011": "You cannot delete",
        "IDS_ERROR0012": "as it is the default setting.",
        "IDS_ERROR0013": "Connection to",
        "IDS_ERROR0014": "could not be established.",
        "IDS_ERROR0015": "The setting",
        "IDS_ERROR0016": "does not exist.",
        "IDS_ERROR0017": "Variable",
        "IDS_ERROR0018": "is not defined",
        "IDS_ERROR0019": "Open Error",
        "IDS_ERROR0020": "Ping Failed",
        "IDS_ERROR0021": "Screen Packet sending Error",
        "IDS_ERROR0022": "Error",
        "IDS_ERROR0023": "A request was made to jump without specifying",
        "IDS_ERROR0024": "the prompt number to jump to.",
        "IDS_ERROR0025": "This was most likely an attempt",
        "IDS_ERROR0026": "to jump to a 'manual' prompt.",
        "IDS_ERROR0027": "Abnormal Connection Failure",
        "IDS_ERROR0028": "Application Aborting!",
        "IDS_ERROR0029": "Application Error",
        "IDS_ERROR0030": "Application Request Error",
        "IDS_ERROR0031": "Attempted SetFocus on uninitialized code.",
        "IDS_ERROR0032": "Attempting to send data while not connected!",
        "IDS_ERROR0033": "Client to Host synchronization compromised.",
        "IDS_ERROR0034": "Bad Start Co-ordinates for",
        "IDS_ERROR0035": "grid area:",
        "IDS_ERROR0036": "Ignoring Jump command.",
        "IDS_ERROR0037": "The printer [",
        "IDS_ERROR0038": "Interrupted by user.",
        "IDS_ERROR0039": "] does not exist. The print job will be sent to your default printer.",
        "IDS_ERROR0040": "Last line from host:",
        "IDS_ERROR0041": "LAST SCRIPT MESSAGE EXECUTED:",
        "IDS_ERROR0042": "NOT USED",
        "IDS_ERROR0043": "Load Error",
        "IDS_ERROR0044": "No Screens have been defined for packet:",
        "IDS_ERROR0045": "Please contact support with the following message:",
        "IDS_ERROR0046": "Print Screen failed.",
        "IDS_ERROR0047": "Program Stopped!",
        "IDS_ERROR0048": "Router Telnet Error",
        "IDS_ERROR0049": "Screen Size too small",
        "IDS_ERROR0050": "Script exceeded maximum allowed commands to perform a single operation.",
        "IDS_ERROR0051": "Script GOSUB jumped to non-existant label resulting in script ending prematurely.",
        "IDS_ERROR0052": "Script is empty.",
        "IDS_ERROR0053": "Script ran out of commands.",
        "IDS_ERROR0054": "Script RETURN finished script early.",
        "IDS_ERROR0055": "Script timed out waiting for a response from the host.",
        "IDS_ERROR0056": "Scripting Error",
        "IDS_ERROR0057": "Shutting down application",
        "IDS_ERROR0058": "System Information Is Unavailable At This Time",
        "IDS_ERROR0059": "The application attempted to continue while the",
        "IDS_ERROR0060": "was modal.",
        "IDS_ERROR0061": "The Copy command is currently disabled.",
        "IDS_ERROR0062": "The passwords do not match.",
        "IDS_ERROR0063": "The Print command is currently disabled.",
        "IDS_ERROR0064": "The script specified with these settings no longer exists.",
        "IDS_ERROR0065": "This parameter",
        "IDS_ERROR0066": "has been disabled.",
        "IDS_ERROR0067": "Timed out waiting for host response",
        "IDS_ERROR0068": "Too many telnet errors",
        "IDS_ERROR0069": "TRACE FROM HOST:",
        "IDS_ERROR0070": "NOT USED",
        "IDS_ERROR0071": "Unable to connect to",
        "IDS_ERROR0072": "Unable to find or run NotePad.exe",
        "IDS_ERROR0073": "Unable to open",
        "IDS_ERROR0074": "file",
        "IDS_ERROR0075": "Unable to start the application.",
        "IDS_ERROR0076": "Unknown parameter specified:",
        "IDS_ERROR0077": "Unknown Script Command",
        "IDS_ERROR0078": "User Interruption",
        "IDS_ERROR0079": "Warning",
        "IDS_ERROR0080": "WGMain.EXE is missing from Bin folder.",
        "IDS_ERROR0081": "You cannot use '/' in setting name.",
        "IDS_ERROR0082": "You must specify a connection name for this connection.",
        "IDS_ERROR0083": "You must specify a host name for this connection.",
        "IDS_ERROR0084": "You must specify a Password to connect.",
        "IDS_ERROR0085": "You must specify a setting to connect.",
        "IDS_ERROR0086": "You must specify a User ID for your password.",
        "IDS_ERROR0087": "You must specify a User ID to connect.",
        "IDS_ERROR0088": "You must specify an account for this connection.",
        "IDS_ERROR0089": "The setting",
        "IDS_ERROR0090": "already exists.  Do you want to replace it?",
        "IDS_ERROR0091": "An error occurred in",
        "IDS_ERROR0092": "General Error",
        "IDS_ERROR0093": "Connection Timeout:\nThe host at the supplied address is not responding, and may be offline. Please try again later.",
        "IDS_ERROR0094": "Connection Refused:\nThe host at the supplied address is not a telnet server. Please enter the address of a telnet server.",
        "IDS_ERROR0095": "Host Not Found:\nThe host address supplied is not recognized. Please confirm the address and try again. ",
        "IDS_ERROR0096": "The Clipboard is currently in use by another application.  Please try again.",
        "IDS_ERROR0097": "Could not establish a secure connection.  Please verify your connection settings and try again.",
        "IDS_ERROR0098": "The following custom dictionary could not be accessed:",
        "IDS_ERROR0099": "Please make sure the dictionary exists in the location specified and you have permission to access the file.  Contact your system administrator for further assistance.",
        "IDS_ERROR0100": "Spelling",
        "IDS_ERROR0101": "Connection Interrupted:\nThe maximum number of users may already be logged on the system.  Please try again later or contact your ",
        "IDS_ERROR0102": " System Administrator.",
        "IDS_ERROR0103": "The Data Path specified is not valid.",
        "IDS_ERROR0104": "Contact your system administrator for further assistance.",
        "IDS_ERROR0105": "Registry Error",
        "IDS_ERROR0106": "Could not save password.",
        "IDS_ERROR0107": "The host requires you to change your password.",
        "IDS_ERROR0108": "User ID or Password failed.",
        "IDS_ERROR0109": "Host has terminated the connection.",
        "IDS_ERROR0110": "Your account is disabled.",
        "IDS_ERROR0111": "The maximum number of users are already logged on the system.  Please try again later.",
        "IDS_ERROR0112": "Account is invalid or doesn't exist.",
        "IDS_ERROR0113": "This version of UniVerse has expired.",
        "IDS_ERROR0114": "Terminal setting is not correct.",
        "IDS_ERROR0115": "Bad Password, Please try again.",
        "IDS_ERROR0116": "Sorry, passwords do not match.",
        "IDS_INF0001": "Contents are proprietary to Campana Systems Inc. and affiliated companies.",
        "IDS_INF0002": "All content is governed by the Software License Agreements.",
        "IDS_INF0003": "NOT USED",
        "IDS_INF0004": "Spelling",
        "IDS_INF0005": "The spelling check is complete.",
        "IDS_INF0006": "The spelling check was canceled.",
        "IDS_INF0007": "Build:",
        "IDS_INF0008": "&copy; 2016 Campana Systems Inc. All rights reserved.",
        "IDS_INF0009": "NOT USED",
        "IDS_INF0010": "Emulation Adjustment",
        "IDS_INF0011": "The Complete Auto Club Information Management System",
        "IDS_INP0001": "Are you sure you want to delete the setting",
        "IDS_INP0002": "NOT USED",
        "IDS_INP0003": "Save as?",
        "IDS_INP0004": "Quit Script?",
        "IDS_INP0005": "Do you want to halt your session?",
        "IDS_MNU0001": "&Copy\tCtrl+C",
        "IDS_MNU0002": "&Delete\tDel",
        "IDS_MNU0003": "&Paste\tCtrl+V",
        "IDS_MNU0004": "&Undo\tCtrl+Z",
        "IDS_MNU0005": "Check Spelling",
        "IDS_MNU0006": "Cu&t\tCtrl+X",
        "IDS_MNU0007": "Select &All",
        "IDS_WEB0004": "Exit",
        "IDS_WEB0005": "Save and Exit",
        "IDS_WEB0006": "Print",
        "IDS_WEB0007": "Input",
        "IDS_WEB0008": "Send",
        "IDS_WEB0009": "Upload",
        "IDS_WEB0010": "File(s) Selected",
        "IDS_WEB0011": "Suggested file path",
        "IDS_WEB0012": "Choose File",
        "IDS_WEB0013": "Upload File",
        "IDS_WEB0015" : "You have been logged out of the application",
        "IDS_WEBWARN0001": "Popups are disabled, <appName> may not work as intended",
        "IDS_WEBERR01": "An entry is required. Please complete this field."
    },
    "fr": {
        "IDS_CAP0001": "OK",
        "IDS_CAP0002": "&Agrave; &propos de",
        "IDS_CAP0003": "&Agrave; propos de",
        "IDS_CAP0004": "&Appliquer",
        "IDS_CAP0005": "A&nnuler",
        "IDS_CAP0006": "Annuler",
        "IDS_CAP0007": "Con&firmer:",
        "IDS_CAP0008": "&Personnaliser...",
        "IDS_CAP0009": "Su&pprimer",
        "IDS_CAP0010": "&Eacute;dit&er",
        "IDS_CAP0011": "Ser&veur",
        "IDS_CAP0012": "Serveur:",
        "IDS_CAP0013": "&OK",
        "IDS_CAP0014": "D&eacute;tachez",
        "IDS_CAP0015": "Mot &de passe:",
        "IDS_CAP0016": "Enregi&strer sous...",
        "IDS_CAP0017": "Con&figuration:",
        "IDS_CAP0018": "Infos &Syst&egrave;me...",
        "IDS_CAP0019": "Code &usager:",
        "IDS_CAP0020": "50% Compl&eacute;t&eacute;",
        "IDS_CAP0021": "Co&mpte:",
        "IDS_CAP0022": "Compte",
        "IDS_CAP0023": "Application",
        "IDS_CAP0024": "Ligne de commande",
        "IDS_CAP0025": "Se connecte &agrave;",
        "IDS_CAP0026": "Connexion",
        "IDS_CAP0027": "&Eacute;diter la configuration",
        "IDS_CAP0028": "Entr&eacute;e",
        "IDS_CAP0029": "Information",
        "IDS_CAP0030": "Ouvrir une session",
        "IDS_CAP0031": "Chemin D'Acc&egrave;s",
        "IDS_CAP0032": "Message",
        "IDS_CAP0033": "D&eacute;cod&eacute;",
        "IDS_CAP0034": "Pr&eacute;paration du fichier pour d&eacute;codage...",
        "IDS_CAP0035": "Question",
        "IDS_CAP0036": "Rapport",
        "IDS_CAP0037": "&Configuration:",
        "IDS_CAP0038": "Sc&ript:",
        "IDS_CAP0039": "Script",
        "IDS_CAP0040": "Saisie d'&eacute;cran",
        "IDS_CAP0041": "Requ&ecirc;te De Script",
        "IDS_CAP0042": "Formulaire D'&Eacute;v&eacute;nement De Scripting",
        "IDS_CAP0043": "D&eacute;marrage Du Script...",
        "IDS_CAP0044": "Le nombre de colonnes a &eacute;t&eacute; ajust&eacute; &agrave;",
        "IDS_CAP0045": "Le nombre de lignes a &eacute;t&eacute; ajust&eacute; &agrave;",
        "IDS_CAP0046": "Cette application requiert une r&eacute;solution graphique minimale de 800 x 600.",
        "IDS_CAP0047": "Traducteur",
        "IDS_CAP0048": "Version",
        "IDS_CAP0049": "Avertissement: Ce logiciel est prot&eacute;g&eacute; par loi du copyright et par les conventions internationales. Toute reproduction ou distribution partielle ou totale du logiciel sans autorisation, par quelque moyen que ce soit, est strictement interdite. Toute personne ne respectant pas ces dispositions se rendra coupable du d&eacute;lit de contrefa&ccedil;on et sera passible des sanctions p&eacute;nales pr&eacute;vues par la loi.",
        "IDS_CAP0050": "Attachez &Agrave; gauche",
        "IDS_CAP0051": "&Session",
        "IDS_CAP0052": "&Fen&ecirc;tre",
        "IDS_CAP0053": "&Aide",
        "IDS_CAP0054": "Standard",
        "IDS_CAP0055": "Dossier parent",
        "IDS_CAP0056": "Im&primer...",
        "IDS_CAP0057": "&Saisie",
        "IDS_CAP0058": "&Visionner",
        "IDS_CAP0059": "Ligne de &commande...",
        "IDS_CAP0060": "Outils de support",
        "IDS_CAP0061": "Enregistrement",
        "IDS_CAP0062": "Observateur de ligne de commande",
        "IDS_CAP0063": "&D&eacute;sactiver la d&eacute;connexion",
        "IDS_CAP0064": "&Quitter",
        "IDS_CAP0065": "NOT USED",
        "IDS_CAP0066": "Imprimer l'&eacute;cran",
        "IDS_CAP0067": "Fermer",
        "IDS_CAP0068": "Pr&eacute;c&eacute;dente",
        "IDS_CAP0069": "Suivante",
        "IDS_CAP0070": "Copier",
        "IDS_CAP0071": "Actualiser",
        "IDS_CAP0072": "Rechercher",
        "IDS_CAP0073": "Zoom",
        "IDS_CAP0074": "&Aide sur AXIS",
        "IDS_CAP0075": "&Aide De GoldCare",
        "IDS_CAP0076": "Lisez l'Accord de Licence",
        "IDS_CAP0077": "Lisez les conditions et les perfectionnements",
        "IDS_CAP0078": "Enregistrement circulaire",
        "IDS_CAP0079": "&Polices...",
        "IDS_CAP0080": "Les &eacute;v&eacute;nements mis en file d'attente ont &eacute;t&eacute; trait&eacute;s. ",
        "IDS_CAP0081": "Aucune activit&eacute; de ligne de commande",
        "IDS_CAP0082": "Activit&eacute; de ligne de commande",
        "IDS_CAP0083": "Activit&eacute; de ligne de commande - Donn&eacute;es sont exig&eacute;es",
        "IDS_CAP0084": "&Initialiser police",
        "IDS_CAP0085": "Port: ",
        "IDS_CAP0086": "Port: ",
        "IDS_CAP0087": "SSL S&eacute;curit&eacute; (&agrave; ",
        "IDS_CAP0088": " bits)",
        "IDS_CAP0089": "Alerte de s&eacute;curit&eacute;",
        "IDS_CAP0090": "Certificat SSL:",
        "IDS_CAP0091": "Distribu&eacute; &agrave;:",
        "IDS_CAP0092": "Distribu&eacute; par:",
        "IDS_CAP0093": "Valide du:",
        "IDS_CAP0094": "Valide jusqu'au",
        "IDS_CAP0095": "&Oui",
        "IDS_CAP0096": "&Non",
        "IDS_CAP0097": "L'information que vous &eacute;changez avec ce serveur ne peut &ecirc;tre visualis&eacute;e ou modifi&eacute;e par d'autres. Cependant, il y a un probl&egrave;me avec le certificat de s&eacute;curit&eacute; du serveur. ",
        "IDS_CAP0098": "Voulez-vous proc&eacute;der avec cette connexion ? ",
        "IDS_CAP0099": "S&eacute;curiser la connexion (SS&L)",
        "IDS_CAP0100": "Certificat",
        "IDS_CAP0101": "L'information que vous &eacute;changez avec ce serveur ne peut &ecirc;tre visualis&eacute;e ou modifi&eacute;e par d'autres.\n\n- Le certificat a &eacute;t&eacute; distribu&eacute; par une autorit&eacute; fi&eacute;e \n- La date de certificat est valide \n- Le certificat a un nom valide",
        "IDS_CAP0102": "Copier",
        "IDS_CAP0103": "R&eacute;duire la grandeur de la police",
        "IDS_CAP0104": "Augmenter la grandeur de la police",
        "IDS_CAP0105": "Coller",
        "IDS_CAP0106": "Transfert augment&eacute; ",
        "IDS_CAP0107": "Transfert regulier",
        "IDS_CAP0108": "Transfert regulier reduit",
        "IDS_CAP0109": "Un rapport qui contient l'information de support correspondant a votre session ",
        "IDS_CAP0110": " et vos r&eacute;sources de l'ordinateur &agrave; &eacute;t&eacute; cr&eacute;&eacute;.",
        "IDS_CAP0111": "Voyez les contenus du rapport",
        "IDS_CAP0112": "Ouvrez le dossier qui contient le rapport",
        "IDS_CAP0113": "Information du session et syst&egrave;me",
        "IDS_CAP0114": "Dossier de donn&eacute;es de support",
        "IDS_CAP0115": "Un rapport contenant les d&eacute;tails de l'erreur a &eacute;t&eacute; cr&eacute;&eacute;.",
        "IDS_CAP0116": "A&nnuler",
        "IDS_CAP0117": "&Dossier parent",
        "IDS_CAP0118": "Contenu du ligne de commande",
        "IDS_CAP0119": "Premier",
        "IDS_CAP0120": "Page pr&eacute;c&eacute;dent",
        "IDS_CAP0121": "Ligne pr&eacute;c&eacute;dent",
        "IDS_CAP0122": "Ligne suivant",
        "IDS_CAP0123": "Page suivant",
        "IDS_CAP0124": "Dernier",
        "IDS_CAP0125": " (Publique)",
        "IDS_CAP0126": "&Nouveau",
        "IDS_CAP0127": "Enregistrer configuration sous...",
        "IDS_CAP0128": "Nom:",
        "IDS_CAP0129": "Configuration commune",
        "IDS_CAP0130": "Enregistrer Sous",
        "IDS_CAP0131": "Afficher ",
        "IDS_CAP0132": " Lignes",
        "IDS_CAP0133": " Colonnes",
        "IDS_CAP0134": "Changer &agrave; ",
        "IDS_CAP0135": "Verrouillage de majuscules activ&eacute;",
        "IDS_CAP0136": "Connecter",
        "IDS_CAP0137": "Connexion au serveur...",
        "IDS_CAP0138": "De liaison...",
        "IDS_CAP0139": "Login",
        "IDS_CAP0140": "mot de passe",
        "IDS_CAP0141": "usager",
        "IDS_CAP0142": "Activer Enregistrement",
        "IDS_CAP0143": "Voyez Enregistrement",
        "IDS_CAP0144": "Recherche",
        "IDS_CAP0145": "Courrier",
        "IDS_CAP0146": "&Commands",
        "IDS_CAP0147": "Authentication Code",
        "IDS_ERROR0001": "n'est pas un lien permis. Aucune action ne sera prise.",
        "IDS_ERROR0002": "Information non envoy&eacute;e. La taille de paquet exc&egrave;de le maximum permis.",
        "IDS_ERROR0003": "Liens externes &agrave; ce document ne sont pas autoris&eacute;s. Aucune action ne sera prise.",
        "IDS_ERROR0004": "Navigation Annul&eacute;e",
        "IDS_ERROR0005": "Erreur De Navigation",
        "IDS_ERROR0006": "NOT USED",
        "IDS_ERROR0007": "Erreur De Transmission",
        "IDS_ERROR0008": "Vous ne pouvez ajouter des mots aux dictionnaires.",
        "IDS_ERROR0009": "Vous pouvez seulement ajouter des mots au",
        "IDS_ERROR0010": "dictionnaire",
        "IDS_ERROR0011": "Vous ne pouvez supprimer",
        "IDS_ERROR0012": "car c'est la configuration par d&eacute;faut.",
        "IDS_ERROR0013": "La connexion &agrave;",
        "IDS_ERROR0014": "n'a pas pu &ecirc;tre &eacute;tabli.",
        "IDS_ERROR0015": "La configuration",
        "IDS_ERROR0016": "n'existe pas.",
        "IDS_ERROR0017": "La variable",
        "IDS_ERROR0018": "n'est pas d&eacute;finie",
        "IDS_ERROR0019": "Erreur D'Ouverture",
        "IDS_ERROR0020": "Le PING A &Eacute;chou&eacute;",
        "IDS_ERROR0021": "erreur en envoyant Le Paquet D'&Eacute;cran",
        "IDS_ERROR0022": "Erreur",
        "IDS_ERROR0023": "Une demande a &eacute;t&eacute; faite pour faire un saut sans indiquer",
        "IDS_ERROR0024": "le num&eacute;ro d'invite vers lequel sauter.",
        "IDS_ERROR0025": "C'&eacute;tait probablement une tentative",
        "IDS_ERROR0026": "de sauter vers un invite 'manuel '.",
        "IDS_ERROR0027": "&Eacute;chec Anormal De Connection",
        "IDS_ERROR0028": "Arr&ecirc;t De L'Application En Cours!",
        "IDS_ERROR0029": "Erreur D'Application",
        "IDS_ERROR0030": "Erreur De Requ&ecirc;te D'Application",
        "IDS_ERROR0031": "Tentative de SetFocus &agrave; partir de code non initialis&eacute;.",
        "IDS_ERROR0032": "Tentative d'envoyer des donn&eacute;es hors connexion!",
        "IDS_ERROR0033": "La synchronisation entre le client et le serveur est compromise.",
        "IDS_ERROR0034": "Mauvaises Coordonn&eacute;es De D&eacute;part pour",
        "IDS_ERROR0035": "le secteur de grille:",
        "IDS_ERROR0036": "Ignorer la commande de Saut.",
        "IDS_ERROR0037": "L'imprimeur [",
        "IDS_ERROR0038": "Interrompu par l'usager.",
        "IDS_ERROR0039": "] n'existe pas. L'imprimante de d&eacute;faut sera utilis&eacute;e &agrave; la place.",
        "IDS_ERROR0040": "Derni&egrave;re ligne re&ccedil;ue du serveur:",
        "IDS_ERROR0041": "DERNIER MESSAGE DU SCRIPT EX&Eacute;CUT&Eacute;:",
        "IDS_ERROR0042": "NOT USED",
        "IDS_ERROR0043": "Erreur De Chargement",
        "IDS_ERROR0044": "Aucun &Eacute;cran n'a &eacute;t&eacute; d&eacute;fini pour le paquet:",
        "IDS_ERROR0045": "SVP Contacter le groupe de support avec le message suivant:",
        "IDS_ERROR0046": "L'Impression D'&Eacute;cran a &eacute;chou&eacute;.",
        "IDS_ERROR0047": "Programme Arr&ecirc;t&eacute;!",
        "IDS_ERROR0048": "Erreur telnet du routeur",
        "IDS_ERROR0049": "Taille D'&Eacute;cran trop petite",
        "IDS_ERROR0050": "Le script a exc&eacute;d&eacute; le nombre maximal de commandes permises pour effectuer une seule op&eacute;ration.",
        "IDS_ERROR0051": "Le script GOSUB a saut&eacute; &agrave; l'&eacute;tiquette non-existant menant &agrave; un arr&ecirc;t pr&eacute;matur&eacute; du script.",
        "IDS_ERROR0052": "Le script est vide.",
        "IDS_ERROR0053": "Le script a manqu&eacute; de commandes.",
        "IDS_ERROR0054": "Le script RETURN a termin&eacute; le script de fa&ccedil;on pr&eacute;matur&eacute;.",
        "IDS_ERROR0055": "Script arr&ecirc;t&eacute; - D&eacute;lai d'attente expir&eacute;, aucune r&eacute;ponse re&ccedil;ue du serveur.",
        "IDS_ERROR0056": "Erreur De Scripting",
        "IDS_ERROR0057": "Fermeture de l'application",
        "IDS_ERROR0058": "L'Information De Syst&egrave;me N'Est Pas Disponible Pr&eacute;sentement",
        "IDS_ERROR0059": "L'application a tent&eacute; de continuer alors que la",
        "IDS_ERROR0060": "&eacute;tait modale",
        "IDS_ERROR0061": "La commande Copier est pr&eacute;sentement d&eacute;sactiv&eacute;e.",
        "IDS_ERROR0062": "Les mots de passe ne correspondent pas.",
        "IDS_ERROR0063": "La commande D'Impression est pr&eacute;sentement d&eacute;sactiv&eacute;e.",
        "IDS_ERROR0064": "Le script associ&eacute; &agrave; ces configurations n'existe plus.",
        "IDS_ERROR0065": "Ce param&egrave;tre",
        "IDS_ERROR0066": "a &eacute;t&eacute; d&eacute;sactiv&eacute;",
        "IDS_ERROR0067": "D&eacute;lai d'attente d&eacute;pass&eacute;, aucune r&eacute;ponse re&ccedil;ue du serveur.",
        "IDS_ERROR0068": "Trop d'erreurs de telnet",
        "IDS_ERROR0069": "TRACE RE&Ccedil;U DU SERVEUR:",
        "IDS_ERROR0070": "NOT USED",
        "IDS_ERROR0071": "Incapable de se connecter &agrave;",
        "IDS_ERROR0072": "Incapable de trouver ou d'activer NotePad.exe",
        "IDS_ERROR0073": "Incapable d'ouvrir",
        "IDS_ERROR0074": "le fichier",
        "IDS_ERROR0075": "Incapable de d&eacute;marrer l'application.",
        "IDS_ERROR0076": "Param&egrave;tre sp&eacute;cifi&eacute; inconnu:",
        "IDS_ERROR0077": "Commande Script Inconnue",
        "IDS_ERROR0078": "Interruption par l'usager",
        "IDS_ERROR0079": "Avertissement",
        "IDS_ERROR0080": "WGMain.EXE manque au dossier Bin.",
        "IDS_ERROR0081": "Vous ne pouvez utiliser '/' en &eacute;tablissant le nom.",
        "IDS_ERROR0082": "Vous devez indiquer un nom de connexion pour cette connexion.",
        "IDS_ERROR0083": "Vous devez indiquer un nom de serveur pour cette connexion.",
        "IDS_ERROR0084": "Vous devez indiquer un mot de passe pour vous connecter.",
        "IDS_ERROR0085": "Vous devez indiquer une configuration vous connecter.",
        "IDS_ERROR0086": "Vous devez entrer un code d'usager pour votre mot de passe.",
        "IDS_ERROR0087": "Vous devez entrer un code d'usager pour vous connecter.",
        "IDS_ERROR0088": "Vous devez indiquer un compte pour cette connexion.",
        "IDS_ERROR0089": "La configuration",
        "IDS_ERROR0090": "existe d&eacute;j&agrave;. Voulez-vous la remplacer?",
        "IDS_ERROR0091": "Une erreur s'est produite dans",
        "IDS_ERROR0092": "Erreur G&eacute;n&eacute;rale",
        "IDS_ERROR0093": "Connection non &eacute;tablie:\nLe serveur &agrave; l'adresse fournie ne r&eacute;pond pas et peut &ecirc;tre d&eacute;connect&eacute;. Svp essayer de nouveau plus tard.",
        "IDS_ERROR0094": "Connection refus&eacute;e:\nLe serveur &agrave; l'adresse fournie n'est pas un serveur telnet. Svp entrer l'adresse d'un serveur telnet.",
        "IDS_ERROR0095": "Serveur non trouv&eacute;:\nL'adresse fournie est inconnue. Svp confirmer l'adresse et essayer de nouveau.",
        "IDS_ERROR0096": "Le presse-papiers est pr&eacute;sentement utilis&eacute; par une autre application. Svp essayer de nouveau.",
        "IDS_ERROR0097": "Une connexion s&eacute;cure n'a pus &ecirc;tre &eacute;tablie. V&eacute;rifier vos configurations de connexion et essayer de nouveau.",
        "IDS_ERROR0098": "Le dictionnaire personnalis&eacute; suivant ne peut pas &ecirc;tre consult&eacute;:",
        "IDS_ERROR0099": "Assurez-vous que le dictionnaire existe &agrave; l'endroit indiqu&eacute; et que vous avez permission &agrave; consult&eacute; le dossier. Contactez votre administrateur de syst&egrave;me si vous avez besoin d'aide.",
        "IDS_ERROR0100": "&Eacute;pellation",
        "IDS_ERROR0101": "Connexion Interrompue:\nLe maximum d'usagers sur le syst&egrave;me peut avoir &eacute;t&eacute; atteint. Svp r&eacute;essayer de nouveau plus tard ou communiquer avec votre administrateur de syst&egrave;me ",
        "IDS_ERROR0102": ".",
        "IDS_ERROR0103": "Le chemin de donn&eacute;es indiqu&eacute;e n'est pas valide.",
        "IDS_ERROR0104": "Contactez votre administrateur de syst&egrave;me si vous avez besoin d'aide.",
        "IDS_ERROR0105": "Erreur Registre",
        "IDS_ERROR0106": "Ne peut pas sauvegarder le mot de passe.",
        "IDS_ERROR0107": "Le serveur exige de changer votre mot de passe.",
        "IDS_ERROR0108": "Le code d'usager ou mot de passe a &eacute;chou&eacute;.",
        "IDS_ERROR0109": "Le serveur a rompu la connexion.",
        "IDS_ERROR0110": "Votre code d'usager est d&eacute;sactiv&eacute;.",
        "IDS_ERROR0111": "Le nombre maximal d'usagers est atteint.  Veuillez r&eacute;essayer plus tard.",
        "IDS_ERROR0112": "Le compte UniVerse est invalide ou inexistant.",
        "IDS_ERROR0113": "Cette version d'UniVerse a expir&eacute;.",
        "IDS_ERROR0114": "La configuration du terminal n'est pas correcte.",
        "IDS_ERROR0115": "Mauvais mot de passe, Veuillez r&eacute;essayer.",
        "IDS_ERROR0116": "Désolé, les mots de passe ne correspondent pas",
        "IDS_INF0001": "Le contenu est la propri&eacute;t&eacute; de Campana Systems Inc. et de ses soci&eacute;t&eacute;s apparent&eacute;es.",
        "IDS_INF0002": "Le contenu est r&eacute;gi par les accords de licence de logiciel.",
        "IDS_INF0003": "NOT USED",
        "IDS_INF0004": "Orthographe",
        "IDS_INF0005": "V&eacute;rification orthographique termin&eacute;e.",
        "IDS_INF0006": "V&eacute;rification orthographique annul&eacute;e.",
        "IDS_INF0007": "Construction:",
        "IDS_INF0008": "&copy; 2016 Campana Systems Inc. Tous droits r&eacute;serv&eacute;s.",
        "IDS_INF0009": "NOT USED",
        "IDS_INF0010": "Ajustement De L'&Eacute;mulation",
        "IDS_INF0011": "Le Syst&egrave;me De Gestion De L'Information Complet De Club Auto",
        "IDS_INP0001": "&Ecirc;tes-vous s&ucirc;r de vouloir supprimer la configuration",
        "IDS_INP0002": "NOT USED",
        "IDS_INP0003": "Enregistrer sous?",
        "IDS_INP0004": "Quitter Le Script?",
        "IDS_INP0005": "Voulez-vous stopper votre session?",
        "IDS_MNU0001": "&Copier\tCtrl+C",
        "IDS_MNU0002": "&Supprimer\tDel",
        "IDS_MNU0003": "C&oller\tCtrl+V",
        "IDS_MNU0004": "&Annuler\tCtrl+Z",
        "IDS_MNU0005": "V&eacute;rifier L'Orthographe",
        "IDS_MNU0006": "C&ouper\tCtrl+X",
        "IDS_MNU0007": "S&eacute;lectionner &Tout",
        "IDS_WEB0001": "Les fichiers sont identiques",
        "IDS_WEB0002": "Confirmer Enregistrement et Fermer",
        "IDS_WEB0003": "Désactivé Enregistrement",
        "IDS_WEB0004": "Fermer",
        "IDS_WEB0005": "Enregistrer et Fermer",
        "IDS_WEB0006": "Imprimer",
        "IDS_WEB0007": "Données",
        "IDS_WEB0008": "Envoyer",
        "IDS_WEB0009": "Téléverser",
        "IDS_WEB0010": "Fichier(s) Choisi",
        "IDS_WEB0011": "Chemin de fichier suggéré",
        "IDS_WEB0012": "Choisir Fichier",
        "IDS_WEB0013": "Téléverser Fichier",
        "IDS_WEB0014": "Quitter la page peut entraîner une perte de données. Êtes-vous sûr de vouloir partir?",
        "IDS_WEB0015" : "Vous avez été déconnecté de l'application",
        "IDS_WEBERR0001": "Erreur pendant comparaison:",
        "IDS_WEBERR0002": "N'a pas reussi a enregistrer le fichier.",
        "IDS_WEBERR0003": "Connection perdue.",
        "IDS_WEBERR0004": "Commande inconnue:",
        "IDS_WEBERR0005": "Vous utilisez un navigateur non pris en charge!  Veuillez passer à Chrome ou MS Edge.",
        "IDS_WEBERR0006": "Êtes-vous sûr de vouloir enregistrer et quitter?",
        "IDS_WEBERR0007": "Connexion perdue, tentative de reconnexion…",
        "IDS_WEBWARN0001": "Les fenêtres contextuelles désactivées, <appName> peuvent ne pas fonctionner comme prévu",
        "IDS_WEBERR01": "Une entrée est requise. Veuillez remplir ce champ."
    }
}


# Language Identifiers
LANG_EN = "en"
LANG_FR = "fr"
