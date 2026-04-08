"""
CV Generator — creates a custom tailored CV as DOCX for each job
"""
import os
import subprocess
import json

def generate_cv(job, profile_data):
    """Generate a custom CV tailored to the job requirements"""
    company   = job["company"]
    role      = job["role"]
    reqs      = job.get("key_requirements", "")
    safe_name = company.replace(" ", "_").replace(".", "").replace(",", "")
    filename  = f"CV_AjatyaGandral_{safe_name}.docx"
    filepath  = os.path.join("cvs", filename)

    # Build tailored summary
    summary = _tailor_summary(profile_data["profile"], role, company, reqs)

    # Select most relevant skills
    skills = _select_skills(profile_data["skills"], reqs)

    # Build JS script
    js = _build_cv_js(profile_data, summary, skills, filename, filepath)
    js_path = f"cvs/gen_{safe_name}.js"

    with open(js_path, "w") as f:
        f.write(js)

    result = subprocess.run(["node", js_path], capture_output=True, text=True)
    os.remove(js_path)

    if result.returncode == 0 and os.path.exists(filepath):
        print(f"  ✅ CV generated: {filename}")
        return filepath
    else:
        print(f"  ❌ CV generation failed: {result.stderr[:200]}")
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
        additions.append("known for proactive delay identification and programme recovery — including recovering a 14 km road project from a 3-week overrun to within 5 days of target")

    summary = base_profile.strip()
    if additions:
        summary += " " + "; ".join(additions) + "."
    return summary

def _select_skills(all_skills, requirements):
    reqs_lower = requirements.lower()
    priority = []
    others   = []
    priority_keywords = ["primavera", "p6", "ms project", "claims", "fidic", "delay",
                         "recovery", "bim", "revit", "autocad", "excel", "site", "hse"]
    for skill in all_skills:
        if any(k in skill.lower() for k in priority_keywords if k in reqs_lower):
            priority.append(skill)
        else:
            others.append(skill)
    combined = priority + others
    return combined[:18]

def _build_cv_js(profile_data, summary, skills, filename, filepath):
    name        = profile_data["name"]
    email       = profile_data["email"]
    phone       = profile_data["phone"]
    experience  = profile_data["experience"]
    education   = profile_data["education"]
    credentials = profile_data["credentials"]

    exp_js = ""
    for exp in experience:
        bullets_js = "\n".join([
            f"""new Paragraph({{numbering:{{reference:'bullets',level:0}},spacing:{{before:40,after:40}},children:[new TextRun({{text:{json.dumps(b)},size:19,font:'Arial',color:'1A1A1A'}})]}})"""
            for b in exp["bullets"]
        ])
        exp_js += f"""
        new Table({{width:{{size:9360,type:WidthType.DXA}},columnWidths:[6500,2860],
          borders:{{top:nb,bottom:nb,left:nb,right:nb,insideH:nb,insideV:nb}},
          rows:[new TableRow({{children:[
            new TableCell({{borders:nbs,width:{{size:6500,type:WidthType.DXA}},children:[new Paragraph({{children:[new TextRun({{text:{json.dumps(exp['title'] + ' | ' + exp['company'])},bold:true,size:20,font:'Arial'}})]}})]}}) ,
            new TableCell({{borders:nbs,width:{{size:2860,type:WidthType.DXA}},children:[new Paragraph({{alignment:AlignmentType.RIGHT,children:[new TextRun({{text:{json.dumps(exp['period'])},size:18,italic:true,font:'Arial',color:'595959'}})]}})]}}),
          ]})]}}) ,
        new Paragraph({{spacing:{{before:20,after:40}},children:[new TextRun({{text:{json.dumps(exp['location'])},size:18,italic:true,font:'Arial',color:'595959'}})]}}),
        {bullets_js},
        new Paragraph({{spacing:{{before:80,after:0}},children:[new TextRun({{text:'',size:18}})]}}),
"""

    edu_js = ""
    for edu in education:
        edu_js += f"""
        new Paragraph({{spacing:{{before:60,after:20}},children:[new TextRun({{text:{json.dumps(edu['degree'])},bold:true,size:20,font:'Arial'}})]}}) ,
        new Paragraph({{spacing:{{before:0,after:20}},children:[new TextRun({{text:{json.dumps(edu['institution'] + ' | ' + edu['period'])},size:18,italic:true,font:'Arial',color:'595959'}})]}}) ,
        new Paragraph({{spacing:{{before:0,after:60}},children:[new TextRun({{text:{json.dumps(edu['focus'])},size:18,font:'Arial',color:'595959'}})]}}),
"""

    cred_js = "\n".join([
        f"""new Paragraph({{numbering:{{reference:'bullets',level:0}},spacing:{{before:40,after:40}},children:[new TextRun({{text:{json.dumps(c)},size:19,font:'Arial'}})]}}),"""
        for c in credentials
    ])

    skills_cells = ""
    cols = 3
    col_w = 3120
    for i in range(0, len(skills), cols):
        row_cells = ""
        for j in range(cols):
            s = skills[i+j] if i+j < len(skills) else ""
            txt = f"✓  {s}" if s else ""
            row_cells += f"""new TableCell({{borders:tb,width:{{size:{col_w},type:WidthType.DXA}},shading:{{fill:'EBF3FB',type:ShadingType.CLEAR}},margins:{{top:60,bottom:60,left:100,right:100}},children:[new Paragraph({{children:[new TextRun({{text:{json.dumps(txt)},size:18,font:'Arial'}})]}})]}}),"""
        skills_cells += f"new TableRow({{children:[{row_cells}]}}),"

    return f"""
const {{Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,
  AlignmentType,BorderStyle,WidthType,ShadingType,LevelFormat}} = require('docx');
const fs = require('fs');

const nb  = {{style:BorderStyle.NONE,size:0,color:'FFFFFF'}};
const nbs = {{top:nb,bottom:nb,left:nb,right:nb}};
const tb  = {{top:{{style:BorderStyle.SINGLE,size:1,color:'CCCCCC'}},bottom:{{style:BorderStyle.SINGLE,size:1,color:'CCCCCC'}},left:{{style:BorderStyle.SINGLE,size:1,color:'CCCCCC'}},right:{{style:BorderStyle.SINGLE,size:1,color:'CCCCCC'}}}};

function sh(text) {{
  return new Paragraph({{
    spacing:{{before:160,after:60}},
    border:{{bottom:{{style:BorderStyle.SINGLE,size:8,color:'1F4E79',space:2}}}},
    children:[new TextRun({{text:text.toUpperCase(),bold:true,size:22,color:'1F4E79',font:'Arial'}})]
  }});
}}

const doc = new Document({{
  numbering:{{config:[{{reference:'bullets',levels:[{{level:0,format:LevelFormat.BULLET,text:'▸',alignment:AlignmentType.LEFT,style:{{paragraph:{{indent:{{left:400,hanging:300}}}}}}}}]}}]}},
  sections:[{{
    properties:{{page:{{size:{{width:12240,height:15840}},margin:{{top:720,right:1080,bottom:720,left:1080}}}}}},
    children:[
      new Table({{width:{{size:9360,type:WidthType.DXA}},columnWidths:[9360],rows:[new TableRow({{children:[new TableCell({{shading:{{fill:'1F4E79',type:ShadingType.CLEAR}},borders:nbs,margins:{{top:160,bottom:160,left:200,right:200}},children:[
        new Paragraph({{alignment:AlignmentType.CENTER,children:[new TextRun({{text:{json.dumps(name)},bold:true,size:40,font:'Arial',color:'FFFFFF'}})]}}),
        new Paragraph({{alignment:AlignmentType.CENTER,children:[new TextRun({{text:'PLANNING ENGINEER',size:24,font:'Arial',color:'BDD7EE'}})]}}),
      ]}})]}})]}}) ,
      new Table({{width:{{size:9360,type:WidthType.DXA}},columnWidths:[9360],rows:[new TableRow({{children:[new TableCell({{shading:{{fill:'EBF3FB',type:ShadingType.CLEAR}},borders:nbs,margins:{{top:80,bottom:80,left:200,right:200}},children:[
        new Paragraph({{alignment:AlignmentType.CENTER,children:[new TextRun({{text:'📧 {email}  |  📞 {phone}  |  UAE Attested Degree  |  Valid Dubai Driving License',size:17,font:'Arial',color:'1F4E79'}})]}}),
      ]}})]}})]}}) ,
      new Paragraph({{spacing:{{before:80,after:0}},children:[new TextRun({{text:''}})]}}) ,
      sh('Professional Summary'),
      new Paragraph({{spacing:{{before:40,after:40}},children:[new TextRun({{text:{json.dumps(summary)},size:19,font:'Arial',color:'1A1A1A'}})]}}),
      sh('Core Competencies'),
      new Table({{width:{{size:9360,type:WidthType.DXA}},columnWidths:[{col_w},{col_w},{col_w}],rows:[{skills_cells}]}}),
      sh('Professional Experience'),
      {exp_js}
      sh('Education'),
      {edu_js}
      sh('Certifications & UAE Credentials'),
      {cred_js}
      sh('Languages'),
      new Paragraph({{spacing:{{before:40,after:40}},children:[new TextRun({{text:'English — Professional Working Proficiency (Written & Spoken)  |  Hindi — Native',size:19,font:'Arial'}})]}}),
    ]
  }}]
}});

Packer.toBuffer(doc).then(buf => {{
  fs.writeFileSync({json.dumps(filepath)}, buf);
  console.log('CV created: {filename}');
}});
"""
