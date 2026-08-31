import { Handle, Position } from '@xyflow/react';

export function KToolNode({ data }: { data: any }) {
  return (
    <div className="ktool-node" data-state={data.runState || 'IDLE'}>
      <div className="node-header">
        <strong>{data.label}</strong>
      </div>
      <div className="node-body">
        <div className="inputs">
          {data.inputs?.map((input: any) => (
            <div key={input.id} style={{ position: 'relative', marginBottom: '8px' }}>
              <Handle
                type="target"
                position={Position.Left}
                id={input.id}
                style={{ top: '50%' }}
                isValidConnection={() => true} // Handled globally by onConnect / isValidConnection
              />
              <span className="handle-label" style={{ paddingLeft: '12px' }}>{input.label}</span>
            </div>
          ))}
        </div>
        <div className="outputs" style={{ textAlign: 'right' }}>
          {data.outputs?.map((output: any) => (
            <div key={output.id} style={{ position: 'relative', marginBottom: '8px' }}>
              <span className="handle-label" style={{ paddingRight: '12px' }}>{output.label}</span>
              <Handle
                type="source"
                position={Position.Right}
                id={output.id}
                style={{ top: '50%' }}
                isValidConnection={() => true}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function MissingNode({ data }: { data: any }) {
  return (
    <div className="missing-node">
      <div>Missing Node</div>
      <div style={{ fontSize: '10px', marginTop: '4px' }}>
        {data.originalType}
      </div>
       <div className="node-body" style={{ marginTop: '8px' }}>
        {/* Render handles so it doesn't break connections in the UI */}
         {data.inputs?.map((input: any) => (
             <Handle key={input.id} type="target" position={Position.Left} id={input.id} />
         ))}
         {data.outputs?.map((output: any) => (
             <Handle key={output.id} type="source" position={Position.Right} id={output.id} />
         ))}
       </div>
    </div>
  );
}
