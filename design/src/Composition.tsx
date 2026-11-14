import { useEffect, useState } from "react";
import { AbsoluteFill, Composition, continueRender, delayRender, getRemotionEnvironment, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import Folder from "./Folder";
import GooeyNav from "./GooeyNav";
import DecryptedText from "./DecryptedText";
import './profile.css';

const navItems = [
  { label: 'Portfolio', href: 'https://bendevelops.vercel.app' },
  { label: 'X', href: 'https://x.com/bennybuild5' },
  { label: 'Thread', href: 'https://trythread.xyz' },
  { label: 'Coffee', href: 'https://buymeacoffee.com/bendevelops' },
];
const documents = [
  { content: <div className="project-page"><b>Thread</b><span>AI companion<br/>Mac + web</span><small>trythread.xyz ↗</small></div> },
  { content: <div className="project-page"><b>Portfolio</b><span>Links +<br/>projects</span><small>bendevelops ↗</small></div> },
  { content: <div className="project-page"><b>Code</b><span>Projects &<br/>experiments</span><small>@BenDevelops01 ↗</small></div> },
];

export const ProfileBanner = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const rendering = getRemotionEnvironment().isRendering;
  const [fontReady] = useState(() => delayRender("Load IBM Plex Mono"));
  useEffect(() => {
    const face = new FontFace("IBM Plex Mono", `url(${staticFile("IBMPlexMono-SemiBold.ttf")})`, {weight:'600'});
    face.load().then(loaded => {document.fonts.add(loaded);continueRender(fontReady);});
  }, [fontReady]);
  return (
    <AbsoluteFill style={{backgroundColor:'#0d1117',color:'#f3f4f6',overflow:'hidden'}}>
      <div style={{position:'absolute',left:64,top:94,fontFamily:'IBM Plex Mono',fontSize:104,fontWeight:600,letterSpacing:'-.035em',lineHeight:1.18}}>
        <DecryptedText text={"hey, i'm\nben."} renderFrame={rendering ? frame : undefined} animateOn="inViewHover" sequential loop loopDelay={4000} speed={45} characters="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%" scrambleColor="#788598" />
      </div>
      <div style={{position:'absolute',left:70,top:360,fontSize:23,color:'#9aa3b0',fontFamily:'sans-serif'}}>building <span style={{color:'#e5e7eb'}}>Thread</span> <span style={{margin:'0 14px',color:'#414958'}}>·</span> Sydney, AU</div>
      <div style={{position:'absolute',left:820,top:205,fontFamily:'sans-serif'}}>
        <Folder
          label="projects"
          color="#496bd4"
          paperColor="#fafafa"
          size={1.1}
          intro={false}
          openOn="hover"
          tilt={0.45}
          bounce={0.2}
          draggable={!rendering}
          zoomOnClick={false}
          items={documents}
          renderProgress={rendering ? 0.5 - 0.5 * Math.cos((frame / durationInFrames) * Math.PI * 2) : undefined}
          onItemClick={(_item: unknown, index: number) => {
            window.location.href = ['https://trythread.xyz','https://bendevelops.vercel.app','https://github.com/BenDevelops01'][index];
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const ProfileNav = () => (
  <AbsoluteFill style={{backgroundColor:'#0d1117',display:'flex',justifyContent:'center',alignItems:'center',fontFamily:'sans-serif'}}>
    <GooeyNav items={navItems} size="lg" frame theme="dark" style={{'--gn-font':'40px','--gn-gap':'0px','--gn-x':'0px','--gn-y':'17px','--gn-pad':'8px'}} className="profile-nav" />
  </AbsoluteFill>
);

export const MyComposition = () => <>
  <Composition id="Benny" component={ProfileBanner} durationInFrames={150} fps={24} width={1200} height={440}/>
  <Composition id="Links" component={ProfileNav} durationInFrames={1} fps={24} width={1200} height={120}/>
</>;
