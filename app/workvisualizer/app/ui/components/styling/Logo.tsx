import { useTheme } from "next-themes";
import dynamic from 'next/dynamic';

const Image = dynamic(() => import('next/image'), { ssr: false });
import ngaDark from "../../../../public/nga-dark.svg";
import ngaLight from "../../../../public/nga-light.svg";

const Logo = () => {
    const { theme } = useTheme();

    return (
        <div>
            <Image
                priority
                src={theme === 'dark' ? ngaDark : ngaLight}
                alt="NGA"
                height={100}
                className="hidden md:block"
            />
        </div>
    );
};

export default Logo;
