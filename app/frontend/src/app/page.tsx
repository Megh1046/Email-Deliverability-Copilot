import { Metadata } from 'next';
import { PageContent } from './PageContent';

export const metadata: Metadata = {
  title: 'Deliverability Copilot',
  description: 'AI-assisted email authentication and deliverability platform',
};

export default function Page() {
  return <PageContent />;
}
