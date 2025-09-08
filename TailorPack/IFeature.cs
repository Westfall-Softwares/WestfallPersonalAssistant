namespace WestfallPersonalAssistant.TailorPack
{
    public interface IFeature
    {
        string Id { get; }
        string Name { get; }
        string Description { get; }
        void Initialize();
        void Shutdown();
    }
}