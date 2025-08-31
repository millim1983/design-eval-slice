import { useEffect, useState } from "react";
import { modelApi } from "../api";

interface ModelForm {
  industry: string;
  name: string;
  version: string;
  path: string;
}

export default function ModelManagerAdmin(){
  const [models, setModels] = useState<any[]>([]);
  const [stats, setStats] = useState<Record<string,number>>({});
  const [form, setForm] = useState<ModelForm>({industry:"", name:"", version:"", path:""});
  const load = async () => {
    const m = await modelApi.list();
    const s = await modelApi.stats();
    setModels(m);
    setStats(s);
  };
  useEffect(()=>{ load(); },[]);
  const submit = async () => {
    await modelApi.register(form);
    setForm({industry:"", name:"", version:"", path:""});
    await load();
  };
  const activate = async (ind:string, name:string) => {
    await modelApi.update(ind, name, {active:true});
    await load();
  };
  return (
    <div className="card">
      <h3>Model Manager Admin</h3>
      <div className="row">
        <input placeholder="Industry" value={form.industry} onChange={e=>setForm({...form, industry:e.target.value})} />
        <input placeholder="Model name" value={form.name} onChange={e=>setForm({...form, name:e.target.value})} />
        <input placeholder="Version" value={form.version} onChange={e=>setForm({...form, version:e.target.value})} />
        <input placeholder="Path" value={form.path} onChange={e=>setForm({...form, path:e.target.value})} />
        <button className="btn" onClick={submit}>Register</button>
      </div>
      <div style={{marginTop:16}}>
        <b>Dataset statistics</b>
        <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(stats,null,2)}</pre>
      </div>
      <div style={{marginTop:16}}>
        <b>Models</b>
        {models.map((m,i)=>(
          <div key={i} className="row" style={{justifyContent:"space-between", borderBottom:"1px solid #333", padding:4}}>
            <span>{m.industry} — {m.name} v{m.version}</span>
            <span>
              {m.active ? <span className="pill">active</span> : <button className="btn" onClick={()=>activate(m.industry,m.name)}>Activate</button>}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
