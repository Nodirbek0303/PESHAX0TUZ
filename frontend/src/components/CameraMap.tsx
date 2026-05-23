import { useMemo, useState } from "react";
import { GoogleMap, InfoWindow, Marker, useJsApiLoader } from "@react-google-maps/api";
import type { Camera } from "../types";

type CameraMapProps = {
  cameras: Camera[];
  selectedCameraId: string;
  onSelect: (camera: Camera) => void;
};

const darkMapStyles: google.maps.MapTypeStyle[] = [
  { elementType: "geometry", stylers: [{ color: "#1d2c4d" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#8ec3b9" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#1a3646" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#304a7d" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#0e1626" }] },
];

export default function CameraMap({ cameras, selectedCameraId, onSelect }: CameraMapProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? "";

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: apiKey,
  });

  const center = useMemo(() => {
    if (cameras.length === 0) return { lat: 41.3, lng: 69.2 };
    const lat = cameras.reduce((sum, camera) => sum + camera.gps_coords.lat, 0) / cameras.length;
    const lng = cameras.reduce((sum, camera) => sum + camera.gps_coords.lon, 0) / cameras.length;
    return { lat, lng };
  }, [cameras]);

  if (!apiKey) {
    return <div className="mini-map map-empty">Google Maps API kaliti sozlanmagan</div>;
  }

  if (loadError) {
    return <div className="mini-map map-empty">Google Maps yuklanmadi</div>;
  }

  if (!isLoaded) {
    return <div className="mini-map map-empty">Xarita yuklanmoqda...</div>;
  }

  const activeCamera = cameras.find((camera) => camera.camera_id === activeId);

  return (
    <GoogleMap
      mapContainerClassName="mini-map"
      center={center}
      zoom={cameras.length === 1 ? 14 : 7}
      options={{
        styles: darkMapStyles,
        disableDefaultUI: true,
        zoomControl: true,
        streetViewControl: false,
        mapTypeControl: false,
      }}
    >
      {cameras.map((camera) => (
        <Marker
          key={camera.camera_id}
          position={{ lat: camera.gps_coords.lat, lng: camera.gps_coords.lon }}
          onClick={() => {
            setActiveId(camera.camera_id);
            onSelect(camera);
          }}
          icon={
            camera.camera_id === selectedCameraId
              ? "http://maps.google.com/mapfiles/ms/icons/blue-dot.png"
              : undefined
          }
        />
      ))}

      {activeCamera && (
        <InfoWindow
          position={{
            lat: activeCamera.gps_coords.lat,
            lng: activeCamera.gps_coords.lon,
          }}
          onCloseClick={() => setActiveId(null)}
        >
          <div className="map-popup">
            <strong>
              №{activeCamera.camera_number} — {activeCamera.camera_name}
            </strong>
            <p>{activeCamera.street}</p>
            <p>{activeCamera.city}</p>
            <p>{activeCamera.status}</p>
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
  );
}
