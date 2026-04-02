import { useAppContext } from '../../context/AppContext';
import './ConfigStrip.css';

export default function ConfigStrip() {
  const { config } = useAppContext();
  const activeType = config.types?.find((t) => t.id === config.activeType);

  return (
    <div className="cfg-strip">
      ENDPOINT&nbsp;
      <span>
        {config.endpoint
          ? config.endpoint.replace(/^https?:\/\//, '')
          : '[ not configured ]'}
      </span>
      &nbsp;&middot;&nbsp;TYPE&nbsp;
      <span>{activeType?.label || '[ not configured ]'}</span>
      &nbsp;&middot;&nbsp;MODEL&nbsp;
      <span>{config.model ? config.model.replace('google/', '') : '[ not configured ]'}</span>
      {config.modality && (
        <>
          &nbsp;&middot;&nbsp;MODALITY&nbsp;
          <span>{config.modality}</span>
        </>
      )}
    </div>
  );
}
