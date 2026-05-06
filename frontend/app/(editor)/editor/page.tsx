import React from "react";
import EditorContainer from "@/components/EditorContainer";
import FixedNav from "@/components/FixedNav";

const EditorPage = () => {
  return (
    <>
      <FixedNav />
      <div className="group flex min-h-screen flex-col items-center justify-center gap-5 bg-neutral-900 md:gap-10">
        <h2 className="wrapper text-center text-5xl font-bold transition-all duration-300 group-focus-within:text-xl group-focus-within:opacity-30">
          Welcome to the SARDS playground
        </h2>
        <EditorContainer />
      </div>
    </>
  );
};
export default EditorPage;
