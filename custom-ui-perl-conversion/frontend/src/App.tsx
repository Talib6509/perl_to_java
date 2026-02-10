import React, { useState, useEffect, useRef } from "react";
import "./carbon.scss";
import "./App.css";
import axios from "axios";
import {
  FileUploader,
  Dropdown,
  TextArea,
  TextAreaSkeleton,
  Button,
  RadioButton,
  RadioButtonGroup,
  CodeSnippet,
  Loading,
  InlineLoading,
} from "carbon-components-react";
import { Add, Reset, AiGenerate, Save } from "@carbon/icons-react";
import logo from "./assets/JLR-Logo.svg";
import saveAs from "file-saver";

function App() {
  const [chunkList, setchunkList] = useState([]);
  const [copybookList, setCopybookList] = useState([]);
  const [selectedChunk, setselectedChunk] = useState("");
  const [analysisType, setAnalysisType] = useState("");
  const [generatedText, setGeneratedText] = useState("");
  const [isExplainLoading, setIsExplainLoading] = useState(false);
  const [isChunkingLoading, setIsChunkingLoading] = useState(false);
  const [isSubmitDisabled, setIsSubmitDisabled] = useState(true);
  const [isSaveDisabled, setisSaveDisabled] = useState(true);
  const [isResetDisabled, setisResetDisabled] = useState(true);
  // const [isAddContextEnabled, setIsAddContextEnabled] = useState(true);
  const [isWatsonxSubmitLoading, setIsWatsonxSubmitLoading] = useState(false);
  const [isJavaConversionSelected, setisJavaConversionSelected] =
    useState(false);
  const [isDB2TablesSelected, setisDB2TablesSelected] = useState("");
  const [isCustomVarSelected, setIsCustomVarSelected] = useState(false);
  const [customQuestion, setCustomQuestion] = useState("");
  const [customVariable, setCustomVariable] = useState("");
  const [db2Data, setDB2] = useState("");
  const [IsDropdownDisabled, setIsDropdownDisabled] = useState(true);
  const [fileName, setFileName] = useState("file");
  const [fileContent, setFileContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingData, setStreamingData] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [disableChunkButtons, setDisabledChunkButtons] = useState(true);
  // const [forFIle, setDisabledChunkButtons] = useState(true);


  //const backend_url =
    //"https://jlr-perl-backend.1jf5e0a9wpt5.eu-de.codeengine.appdomain.cloud";
  const backend_url = "http://127.0.0.1:5000";

   useEffect(() => {
    console.log('isSubmitDisabled state has changed:', isSubmitDisabled);
    // Perform any additional actions based on the state change
  }, [isSubmitDisabled]);

  const handleFileUpload = (event: any) => {
    setselectedChunk("");
    setGeneratedText("");
    setCustomQuestion("");
    setCustomVariable("");
    setStreamingData("");
    
    const file = event.target.files?.[0];
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const content = e.target?.result;
      if (typeof content === 'string') {
        setFileContent(content);
      }
    };

    reader.readAsText(file);

    // collect file and set filename variable
    // const file = event.target.files[0];
    setDB2(file);
    setFileName(file['name']);

    // append into form data so that it can be used with our Flask backend API
    const formData = new FormData();
    formData.append("file", file);
    console.log(formData);

    // using local dev API or prod from Code Engine
    console.log(backend_url);
    console.log("Upload triggered, sending file to backend end for chunking");

    // loading screen whilst chunking is taking place
    setIsChunkingLoading(true);
    
      // hit our backend Chunk endpoint, runs an algorithm over the code to generate chunks from file (due to prompt size limitation)
    axios
      .post(`${backend_url}/chunk`, formData, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "content-type": "multipart/form-data",
          "char-limit": 5000,
          "request-type": "upload",
          "store-chunks": "false",
          "new-collection": "false",
          "file-name": file['name'],
        },
      })
      .then((res) => {
        setchunkList(res.data.chunks);
        setIsChunkingLoading(false);
        console.log(file['name']);   
      

        // check the analysis type state
        console.log(
          "Analysis Type Collected whilst chunking took place: ",
          analysisType
        );

        // use chunkList to determine if chunking has taken place and thus a file is uploaded

        // check the state of analysisType and see if user has selected list db2 tables. Everything requires dropdown apart from list db2 tables
        if (analysisType === "convert_whole_part") {
          console.log("Analysis Type: ", analysisType);
          // enable to submit button (disabled on page load)
          setIsSubmitDisabled(false);
          //
          setIsDropdownDisabled(true);
        } else if (analysisType === "convert_full" || analysisType === "explain_full") {
          setIsSubmitDisabled(false);
          setIsDropdownDisabled(true);
        }
        else {
          // if analysis type is not db2 tables then enable the dropdown
          setIsDropdownDisabled(false);
        }
      })
      .catch(error => {
        console.error('Error fetching data:', error);
      });
  };

  const handleFileDelete = () => {
    // upoon file removal
    setselectedChunk("");
    setGeneratedText("");
    setchunkList([]);
    setIsSubmitDisabled(true);
    setStreamingData("");
    setDisabledChunkButtons(true);
  };

  // upon selecting from dropdown
  const handleChunkSelection = (event: any) => {
      setselectedChunk(event.selectedItem);
      setIsSubmitDisabled(false);
      setGeneratedText("");
      setStreamingData("");
      setDisabledChunkButtons(false);
  };


  // upon selection of custom input from radio button, select and set the values
  const handleJavaConversion = (event: any) => {
    if (isJavaConversionSelected) {
      setCustomQuestion(event.target.value);
    } else {
      setCustomVariable(event.target.value);
    }
  };

  const handleSaveResponse = () => {
    // Assuming 'generatedText' is your text variable you want to save

    // Create a Blob from the text
    let blob = new Blob(
      [
        `<html><head><meta charset="utf-8"></head><body>${streamingData}</body></html>`,
      ],
      { type: "application/msword" }
    );

    // Use FileSaver.js to save the file
    saveAs(blob, "generatedText.doc");
  };

  const handleGenerateSelection = async (event: any) => {

    // loading screens enabled
    setIsExplainLoading(true);
    setIsWatsonxSubmitLoading(true);

    // check status of analysis type
    console.log("Explain endpoint with analysis type: ", analysisType);

    // check the state of db2 tables from handleRadioButton, if true then disbles dropdown and calls function
    if (isDB2TablesSelected === "selected") {
      console.log("DB2 List Has Been Selected");
      setIsDropdownDisabled(true);
    } else if (analysisType === "convert_full" || analysisType === "explain_full") {
      setIsDropdownDisabled(true);
      setIsSubmitDisabled(false);

      try{
        setStreamingData('');
        setIsStreaming(true);
        setisSaveDisabled(true);
        // setisResetDisabled(true);

        const response = await fetch(`${backend_url}/explain`, {
          method: "POST",
          headers: {
            "Access-Control-Allow-Origin": "*",
            "content-type": "multipart/form-data",
            "analysis-type": analysisType,
          },
          body: JSON.stringify({data: fileContent})
        });

        // loading screens disabled
        setIsExplainLoading(false);
        setIsWatsonxSubmitLoading(false);

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder()
        
        const readStream = async () => {
          reader?.read().then(function processText({ done, value }) {
            if (done) {
              setIsStreaming(false);
              setisSaveDisabled(false);
              
              return
            }
            const chunk = decoder.decode(value, { stream: true });
            // console.log('chunk===>', chunk);
            setStreamingData((prevData) => prevData + chunk);
            readStream();
          })
        };
        readStream();
      }catch (error) {
        console.error("Error fetching the stream:", error);
      }

      // // enable save and reset buttons
      // if (!isStreaming && streamingData){
      //   setisSaveDisabled(false);
      setisResetDisabled(false);
      // }

    }
    else {
      try{
        setStreamingData('');
        setIsStreaming(true);
        setisSaveDisabled(true);
        // setisResetDisabled(true);

        const response = await fetch(`${backend_url}/explain`, {
          method: "POST",
          headers: {
            "Access-Control-Allow-Origin": "*",
            "content-type": "multipart/form-data",
            "analysis-type": analysisType,
          },
          body: JSON.stringify({data: selectedChunk})
        });

        // loading screens disabled
        setIsExplainLoading(false);
        setIsWatsonxSubmitLoading(false);

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder()
        
        const readStream = async () => {
          reader?.read().then(function processText({ done, value }) {
            if (done) {
              setIsStreaming(false);
              setisSaveDisabled(false);
              // setisResetDisabled(false);
              return
            }
            const chunk = decoder.decode(value, { stream: true });
            // console.log('chunk===>', chunk);
            setStreamingData((prevData) => prevData + chunk);
            readStream();
          })
        };
        readStream();
      }catch (error) {
        console.error("Error fetching the stream:", error);
      }
      
      // enable save and reset buttons
      // setisSaveDisabled(false);
      setisResetDisabled(false);
    }
  };

  // refresh button reloads page
  const refresh = () => {
    window.location.reload();
  };

  // triggered by onChange anytime radio button is interacted with
  const handleRadioSelect = (event: any) => {
    // initailly collect and store the analysis type from id of the button
    const analysisType = event.target.id;
    setAnalysisType(analysisType);

    // if the chunkList is not empty i,e file has been uploaded
    if (chunkList.length > 0) {
      setGeneratedText("");
      setStreamingData("");

      if (analysisType === "explain") {
        setIsDropdownDisabled(false);
        setisDB2TablesSelected("");
        setIsCustomVarSelected(false);
        setisJavaConversionSelected(false);
        if (selectedChunk){
          setIsSubmitDisabled(false)
        }else{
        setIsSubmitDisabled(true)}
      } else if (analysisType === "conversion") {
        setisJavaConversionSelected(true);
        setIsCustomVarSelected(false);
        setIsDropdownDisabled(false);
        setisDB2TablesSelected("");
        if (selectedChunk){
          setIsSubmitDisabled(false)
        }else{
        setIsSubmitDisabled(true)
        }
      } else if (analysisType === "convert_full") {
        setIsCustomVarSelected(false);
        setisJavaConversionSelected(true);
        setIsDropdownDisabled(true);
        setIsSubmitDisabled(false);
        setisDB2TablesSelected("");
      } else if (analysisType === "explain_full") {
        setIsCustomVarSelected(false);
        setisJavaConversionSelected(false);
        setIsDropdownDisabled(true);
        setIsSubmitDisabled(false);
        setisDB2TablesSelected("");
      }
      {/*else if (analysisType === "db2") {
        setIsSubmitDisabled(false);
        setIsDropdownDisabled(true);
        setIsCustomVarSelected(false);
        setisJavaConversionSelected(false);
        setisDB2TablesSelected("selected");
        setGeneratedText("");
        setselectedChunk("");
      } else if (analysisType === "rule") {
        setIsSubmitDisabled(false);
        setIsDropdownDisabled(true);
        setIsCustomVarSelected(false);
        setisJavaConversionSelected(false);
        setisDB2TablesSelected("");
        setGeneratedText("");
      } else {
        setisDB2TablesSelected("");
      }*/}
      // if no file has been uploaded the following logic is ran:
    } else {
      setGeneratedText("");
      setStreamingData("");
      if(fileContent){
        setIsCustomVarSelected(false);
        setIsDropdownDisabled(true);
        setIsSubmitDisabled(false);
        setisDB2TablesSelected("");
      } else {
        setIsDropdownDisabled(true);
        setIsSubmitDisabled(true);
      }
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.scrollTop = textareaRef.current.scrollHeight;
    }
  }, [streamingData]);

  return (
    <div className="App">
      <div className="sidebar">
      <div className="sidebar-logo">
          <img src={logo} alt="logo"></img>
        </div>
        <div className="browse-button-container">
          <FileUploader className="upload-button"
            labelTitle=""
            buttonLabel="Upload File"
            labelDescription=""
            buttonKind="primary"
            size="md"
            filenameStatus="edit"
            accept={[".pl"]}
            multiple={false}
            disabled={false}
            iconDescription="Delete file"
            name=""
            onChange={handleFileUpload}
            onDelete={handleFileDelete}
          />
          <p className="upload-button-text">Max file size is 200mb. Supported file types are .PL</p>
          <hr/>
        </div>
        <div className="radio-button-container">
          <p className="radio-text">Generate Actions:</p>
          <RadioButtonGroup
            name="radio button group"
            orientation="vertical"
          >
          <p className="radio-text">For File:</p>
            <RadioButton
              labelText="Explain"
              name="explain_full"
              value="explain_full"
              id="explain_full"
              onClick={handleRadioSelect}
            ></RadioButton>
            <RadioButton
              labelText="Java Conversion"
              name="convert_full"
              value="convert_full"
              id="convert_full"
              onClick={handleRadioSelect}
            ></RadioButton>
            <br></br>
          <p className="radio-text">For Chunk:</p>
          <RadioButton
              labelText="Explain"
              name="explain"
              value="explain"
              id="explain"
              onClick={handleRadioSelect}
              disabled={disableChunkButtons}
            ></RadioButton>
            <RadioButton
              labelText="Java Conversion"
              value="conversion"
              id="conversion"
              onClick={handleRadioSelect}
              disabled={disableChunkButtons}
            ></RadioButton>
          </RadioButtonGroup>
        </div>
        <div className="submit-button-container">
          <Button
            renderIcon={AiGenerate}
            className="submit-button"
            onClick={handleGenerateSelection}
            disabled={isSubmitDisabled}
          >
            Generate
          </Button>
        </div>
     
        {isWatsonxSubmitLoading ? (
          <div className="loading-resp">
            <InlineLoading
              status="active"
              iconDescription="Loading"
              description="Loading response..."
            />
          </div>
        ) : (
          <div></div>
        )}
      </div>

      {isChunkingLoading ? <Loading /> : <p></p>}

      <div className="maincontent">
        <p className="dropdown-text">Chunks ({chunkList.length})</p>
        <div className="dropdownDiv">
          <Dropdown
            className="dropdown"
            id="dropdown"
            titleText="Dropdown"
            helperText="Upload a file to view chunks"
            initialSelectedItem={chunkList[0]}
            label=""
            items={chunkList}
            hideLabel={true}
            disabled={IsDropdownDisabled}
            onChange={handleChunkSelection}
            selectedItem={selectedChunk}
          />
        </div>
        <div className="code-cobol-watsonx-container">
          <div className="cobolTextAreaDiv">
            {/* <TextArea
              labelText="Code:"
              value={selectedChunk}
              rows={20}
              id="text-area-1"
              disabled={false}
            /> */}
            <p className="code-text">Code from {fileName}:</p>
            <CodeSnippet
              type="multi"
              feedback="Copied to clipboard"
              minCollapsedNumberOfRows={28}
              maxExpandedNumberOfRows={28}
              showMoreText=""
              showLessText=""
            >
              {(analysisType === 'convert_full' || analysisType === 'explain_full') && <pre>{fileContent}</pre>}
              {selectedChunk}
            </CodeSnippet>
          </div>

          <div className="generatedTextAreaDiv">
            {(
              <TextArea
                className="text-area-font"
                labelText="Generated by watsonx.ai:"
                value={streamingData}
                rows={23}
                id="text-area-1"
                disabled={false}
                ref={textareaRef}
              />
            )}
          </div>
        </div>

        <div className="save-reset-buttons">
          <Button
            renderIcon={Save}
            disabled={isSaveDisabled}
            onClick={handleSaveResponse}
          >
            Save Response
          </Button>
          <Button
            renderIcon={Reset}
            kind="secondary"
            disabled={isResetDisabled}
            onClick={refresh}
          >
            Reset
          </Button>
        </div>
      </div>
    </div>
  );
}

export default App;
