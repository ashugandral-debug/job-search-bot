"""
CV Generator — creates a custom tailored CV as DOCX for each job
"""
import os
import subprocess
import json

def generate_cv(job, profile_data):
    company   = job["company"]
    role      = job["role"]
    reqs      = job.get("key_requirements", "")
    safe_name = company.replace(" ", "_").replace(".", "").replace(",", "")
    filename  = "CV_AjatyaGandral_" + safe_name + ".docx"
    filepath  = os.path.join("cvs", filename)

    summary  = _tailor_summary(profile_data["profile"], role, company, reqs)
    skills   = _select_skills(profile_data["skills"], reqs)
    js       = _build_cv_js(profile_data, summary, skills, filename, filepath)
    js_path  = "cvs/gen_" + safe_name + ".js"

    with open(js_path, "w") as f:
        f.write(js)

    result = subprocess.run(["node", js_path], capture_output=True, text=True)
    os.remove(js_path)

    if result.returncode == 0 and os.path.exists(filepath):
        print("  CV generated: " + filename)
        return filepath
    else:
        print("  CV generation failed: " + result.stderr[:200])
        return None


def _tailor_summary(base_profile, role, company, requirements):
    reqs_lower = requirements.lower()
    additions = []
    if "claims" in reqs_lower or "fidic" in reqs_lower:
        additions.append("experienced in FIDIC contract management and claims-related documentation")
    if "site" in reqs_lower or "supervision" in reqs_lower:
        additions.append("with proven site supervision and HSE compliance track record")
    if "consultancy" in reqs_lower or "consultant" in reqs_lower:
        additions.append("bringing a consultancy-oriented mindset and multi-level reporting capabilities")
    if "building" in reqs_lower or "construction" in reqs_lower:
        additions.append("specialising in building construction project scheduling and milestone control")
    if "recovery" in reqs_lower or "delay" in reqs_lower:
        additions.append("known for proactive delay identification and programme recovery")
    summary = base_profile.strip()
    if additions:
        summary += " " + "; ".join(additions) + "."
    return summary


def _select_skills(all_skills, requirements):
    reqs_lower = requirements.lower()
    priority, others = [], []
    keywords = ["primavera","p6","ms project","claims","fidic","delay",
                "recovery","bim","revit","autocad","excel","site","hse"]
    for skill in all_skills:
        if any(k in skill.lower() for k in keywords if k in reqs_lower):
            priority.append(skill)
        else:
            others.append(skill)
    return (priority + others)[:18]


def _build_cv_js(profile_data, summary, skills, filename, filepath):
    name        = profile_data["name"]
    email       = profile_data["email"]
    phone       = profile_data["phone"]
    experience  = profile_data["experience"]
    education   = profile_data["education"]
    credentials = profile_data["credentials"]
    col_w       = 3120

    # Skills rows
    skills_rows = ""
    for i in range(0, len(skills), 3):
        cells = ""
        for j in range(3):
            s   = skills[i+j] if i+j < len(skills) else ""
            txt = ("* " + s) if s else ""
            cells += (
                "new TableCell({"
                "borders:tb,"
                "width:{size:" + str(col_w) + ",type:WidthType.DXA},"
                "shading:{fill:'EBF3FB',type:ShadingType.CLEAR},"
                "margins:{top:60,bottom:60,left:100,right:100},"
                "children:[new Paragraph({children:[new TextRun({"
                "text:" + json.dumps(txt) + ","
                "size:18,font:'Arial'"
                "})]})]"
                "}),"
            )
        skills_rows += "new TableRow({children:[" + cells + "]}),"

    # Experience blocks
    exp_js = ""
    for exp in experience:
        bullets = ""
        for b in exp["bullets"]:
            bullets += (
                "new Paragraph({"
                "numbering:{reference:'bullets',level:0},"
                "spacing:{before:40,after:40},"
                "children:[new TextRun({"
                "text:" + json.dumps(b) + ","
                "size:19,font:'Arial',color:'1A1A1A'"
                "})]}),"
            )
        exp_js += (
            "new Table({"
            "width:{size:9360,type:WidthType.DXA},"
            "columnWidths:[6500,2860],"
            "borders:{top:nb,bottom:nb,left:nb,right:nb,insideH:nb,insideV:nb},"
            "rows:[new TableRow({children:["
            "new TableCell({borders:nbs,width:{size:6500,type:WidthType.DXA},"
            "children:[new Paragraph({children:[new TextRun({"
            "text:" + json.dumps(exp["title"] + " | " + exp["company"]) + ","
            "bold:true,size:20,font:'Arial'"
            "})]})]}),"
            "new TableCell({borders:nbs,width:{size:2860,type:WidthType.DXA},"
            "children:[new Paragraph({alignment:AlignmentType.RIGHT,"
            "children:[new TextRun({"
            "text:" + json.dumps(exp["period"]) + ","
            "size:18,italic:true,font:'Arial',color:'595959'"
            "})]})]}),"
            "]})]}),"
            "new Paragraph({spacing:{before:20,after:40},"
            "children:[new TextRun({"
            "text:" + json.dumps(exp["location"]) + ","
            "size:18,italic:true,font:'Arial',color:'595959'"
            "})]}),"
            + bullets +
            "new Paragraph({spacing:{before:80,after:0},children:[new TextRun({text:'',size:18})]}),"
        )

    # Education blocks
    edu_js = ""
    for edu in education:
        edu_js += (
            "new Paragraph({spacing:{before:60,after:20},"
            "children:[new TextRun({"
            "text:" + json.dumps(edu["degree"]) + ","
            "bold:true,size:20,font:'Arial'"
            "})]}),"
            "new Paragraph({spacing:{before:0,after:20},"
            "children:[new TextRun({"
            "text:" + json.dumps(edu["institution"] + " | " + edu["period"]) + ","
            "size:18,italic:true,font:'Arial',color:'595959'"
            "})]}),"
            "new Paragraph({spacing:{before:0,after:60},"
            "children:[new TextRun({"
            "text:" + json.dumps(edu["focus"]) + ","
            "size:18,font:'Arial',color:'595959'"
            "})]}),"
        )

    # Credentials
    cred_js = ""
    for c in credentials:
        cred_js += (
            "new Paragraph({"
            "numbering:{reference:'bullets',level:0},"
            "spacing:{before:40,after:40},"
            "children:[new TextRun({"
            "text:" + json.dumps(c) + ","
            "size:19,font:'Arial'"
            "})]}),"
        )

    contact_line = "Email: " + email + "  |  Phone: " + phone + "  |  UAE Attested Degree  |  Valid Dubai Driving License"

    js = (
        "const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,"
        "AlignmentType,BorderStyle,WidthType,ShadingType,LevelFormat} = require('docx');\n"
        "const fs = require('fs');\n\n"
        "const nb  = {style:BorderStyle.NONE,size:0,color:'FFFFFF'};\n"
        "const nbs = {top:nb,bottom:nb,left:nb,right:nb};\n"
        "const tb  = {\n"
        "  top:{style:BorderStyle.SINGLE,size:1,color:'CCCCCC'},\n"
        "  bottom:{style:BorderStyle.SINGLE,size:1,color:'CCCCCC'},\n"
        "  left:{style:BorderStyle.SINGLE,size:1,color:'CCCCCC'},\n"
        "  right:{style:BorderStyle.SINGLE,size:1,color:'CCCCCC'}\n"
        "};\n\n"
        "function sh(text) {\n"
        "  return new Paragraph({\n"
        "    spacing:{before:160,after:60},\n"
        "    border:{bottom:{style:BorderStyle.SINGLE,size:8,color:'1F4E79',space:2}},\n"
        "    children:[new TextRun({text:text.toUpperCase(),bold:true,size:22,color:'1F4E79',font:'Arial'})]\n"
        "  });\n"
        "}\n\n"
        "const doc = new Document({\n"
        "  numbering:{config:[{reference:'bullets',levels:[{\n"
        "    level:0,format:LevelFormat.BULLET,text:'*',\n"
        "    alignment:AlignmentType.LEFT,\n"
        "    style:{paragraph:{indent:{left:400,hanging:300}}}\n"
        "  }]}]},\n"
        "  sections:[{\n"
        "    properties:{page:{size:{width:12240,height:15840},margin:{top:720,right:1080,bottom:720,left:1080}}},\n"
        "    children:[\n"
        "      new Table({width:{size:9360,type:WidthType.DXA},columnWidths:[9360],rows:[new TableRow({children:[new TableCell({\n"
        "        shading:{fill:'1F4E79',type:ShadingType.CLEAR},borders:nbs,\n"
        "        margins:{top:160,bottom:160,left:200,right:200},\n"
        "        children:[\n"
        "          new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:" + json.dumps(name) + ",bold:true,size:40,font:'Arial',color:'FFFFFF'})]}),\n"
        "          new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:'PLANNING ENGINEER',size:24,font:'Arial',color:'BDD7EE'})]})\n"
        "        ]\n"
        "      })]})]}),\n"
        "      new Table({width:{size:9360,type:WidthType.DXA},columnWidths:[9360],rows:[new TableRow({children:[new TableCell({\n"
        "        shading:{fill:'EBF3FB',type:ShadingType.CLEAR},borders:nbs,\n"
        "        margins:{top:80,bottom:80,left:200,right:200},\n"
        "        children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:" + json.dumps(contact_line) + ",size:17,font:'Arial',color:'1F4E79'})]})]\n"
        "      })]})]}),\n"
        "      new Paragraph({spacing:{before:80,after:0},children:[new TextRun({text:''})]}),\n"
        "      sh('Professional Summary'),\n"
        "      new Paragraph({spacing:{before:40,after:40},children:[new TextRun({text:" + json.dumps(summary) + ",size:19,font:'Arial',color:'1A1A1A'})]}),\n"
        "      sh('Core Competencies'),\n"
        "      new Table({width:{size:9360,type:WidthType.DXA},columnWidths:[" + str(col_w) + "," + str(col_w) + "," + str(col_w) + "],rows:[" + skills_rows + "]}),\n"
        "      sh('Professional Experience'),\n"
        + exp_js +
        "      sh('Education'),\n"
        + edu_js +
        "      sh('Certifications & UAE Credentials'),\n"
        + cred_js +
        "      sh('Languages'),\n"
        "      new Paragraph({spacing:{before:40,after:40},children:[new TextRun({text:'English - Professional Working Proficiency  |  Hindi - Native',size:19,font:'Arial'})]}),\n"
        "    ]\n"
        "  }]\n"
        "});\n\n"
        "Packer.toBuffer(doc).then(buf => {\n"
        "  fs.writeFileSync(" + json.dumps(filepath) + ", buf);\n"
        "  console.log('CV created: " + filename + "');\n"
        "});\n"
    )
    return js
